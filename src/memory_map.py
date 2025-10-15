import re
from typing import List, Dict, Tuple
import networkx as nx
from pyvis.network import Network
import spacy
from collections import defaultdict
import streamlit as st
import streamlit.components.v1 as components
import tempfile
import random
from langchain_ollama import OllamaLLM

# Initialize spaCy model
def ensure_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        import sys
        import subprocess
        
        st.info("📥 Downloading required language model. This may take a moment...")
        
        # Use the Python executable from the current environment
        python_exe = sys.executable
        subprocess.run([python_exe, "-m", "pip", "install", "spacy"])
        subprocess.run([python_exe, "-m", "spacy", "download", "en_core_web_sm"])
        
        return spacy.load("en_core_web_sm")

# Load the model
nlp = ensure_spacy_model()

def extract_concepts_and_relations(text: str) -> Tuple[list, list]:
    """Extract key concepts and their relationships from text."""
    doc = nlp(text)
    
    # Extract main concepts (nouns and noun phrases)
    concepts = []
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:  # Limit to phrases of 3 words or less
            concepts.append(chunk.text.strip().lower())
    
    # Extract relationships between concepts
    relations = []
    for sent in doc.sents:
        sent_concepts = [chunk.text.strip().lower() for chunk in sent.noun_chunks if len(chunk.text.split()) <= 3]
        
        # Create relationships between concepts in the same sentence
        for i in range(len(sent_concepts)):
            for j in range(i + 1, len(sent_concepts)):
                relations.append((sent_concepts[i], sent_concepts[j]))
    
    return list(set(concepts)), list(set(relations))

def get_concept_description(llm: OllamaLLM, concept: str, context: str) -> str:
    """Use LLM to generate a meaningful description for a concept based on its context."""
    prompt = f"""Given the concept "{concept}" from the document, create a concise but informative tooltip that explains:

1. What this concept means in the context
2. Its key relationships or importance
3. Any relevant examples or specific details

Use the following context to inform your description:

Context: {context}

Format your response as a clear, bulleted list with 2-3 key points. Keep each point concise but meaningful.
Response:"""
    
    try:
        response = llm.invoke(prompt)
        # Process response to ensure clean bullet points
        lines = response.strip().split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('•') and not line.startswith('-'):
                line = '• ' + line
            if line:
                formatted_lines.append(line)
        return '\n'.join(formatted_lines)
    except:
        # Fallback with a more informative generic message
        return (f"• '{concept}' is a key concept in the document\n"
                "• Hover over connected nodes to explore relationships")

def create_mermaid_mindmap(concepts: set, concept_connections: dict, edge_weights: dict, levels: dict) -> str:
    """Generate a Mermaid mindmap chart."""
    mermaid_code = ["mindmap"]
    
    def clean_concept(concept):
        """Clean concept text for Mermaid compatibility."""
        return concept.replace("(", "<").replace(")", ">").replace("[", "{").replace("]", "}")
    
    def add_concepts(parent, level, added=None):
        if added is None:
            added = set()
        
        # Get all concepts at this level that are connected to the parent
        concepts_at_level = [
            c for c in concepts 
            if levels.get(c) == level and c not in added
            and any((parent, c) in edge_weights or (c, parent) in edge_weights)
        ]
        
        if not concepts_at_level:
            return
        
        indent = "    " * level
        for concept in concepts_at_level:
            mermaid_code.append(f"{indent}* {clean_concept(concept)}")
            added.add(concept)
            add_concepts(concept, level + 1, added)
    
    # Start with root node
    root = min(levels.items(), key=lambda x: x[1])[0]
    mermaid_code.append(f"root(({clean_concept(root)}))")
    add_concepts(root, 1, {root})
    
    # Add any remaining unconnected concepts at the end
    remaining = concepts - set(c for line in mermaid_code for c in [line.strip("* ")])
    if remaining:
        mermaid_code.append("    * Other Concepts")
        for concept in remaining:
            mermaid_code.append(f"        * {clean_concept(concept)}")
    
    return "\n".join(mermaid_code)

def create_memory_map(documents: List[dict], min_connections: int = 2, 
                     theme: str = "light", node_size: bool = True) -> str:
    """
    Create an interactive memory map visualization.
    
    Args:
        documents: List of document chunks
        min_connections: Minimum number of connections for a concept to be included
        theme: Color theme ('light' or 'dark')
        node_size: Whether to size nodes based on connections
        viz_type: Type of visualization ('Interactive Graph' or 'Mermaid Mindmap')
    """
    
    # Combine all document contents
    all_text = " ".join([doc.page_content for doc in documents])
    
    # Extract concepts and relations
    concepts, relations = extract_concepts_and_relations(all_text)
    
    # Create graph
    G = nx.Graph()
    
    # Add nodes and edges with weights
    edge_weights = defaultdict(int)
    for source, target in relations:
        edge_weights[(source, target)] += 1
    
    # Count connections for each concept
    concept_connections = defaultdict(int)
    for (source, target), weight in edge_weights.items():
        concept_connections[source] += weight
        concept_connections[target] += weight
    
    # Also include concepts that appear in the text but might not have connections
    for concept in concepts:
        if concept not in concept_connections:
            concept_connections[concept] = 1
    
    # First try to get concepts meeting minimum connections
    significant_concepts = {concept for concept, count in concept_connections.items() 
                          if count >= min_connections}
    
    # If we don't have enough concepts, take the top N most connected ones
    if len(significant_concepts) < 5:  # Ensure we have at least 5 concepts if available
        sorted_concepts = sorted(concept_connections.items(), key=lambda x: x[1], reverse=True)
        significant_concepts = set(concept for concept, _ in sorted_concepts[:max(5, len(sorted_concepts))])
    
    # Set up theme colors
    if theme == "dark":
        bgcolor = "#222222"
        font_color = "#ffffff"
        node_color = "#7f7fff"
        edge_color = "#666666"
    else:
        bgcolor = "#ffffff"
        font_color = "#000000"
        node_color = "#0000ff"
        edge_color = "#999999"
    
    # Create visualization network
    net = Network(height="600px", width="100%", bgcolor=bgcolor, font_color=font_color)
    
    # Initialize LLM for concept descriptions
    llm = OllamaLLM(model="gemma")
    
    # Always ensure we have at least some concepts to display
    if not significant_concepts and concepts:
        # If we have no significant concepts but have some concepts, take the first few
        significant_concepts = set(list(concepts)[:5])
        st.info("Showing the first few concepts found in the document.")
    elif not concepts:
        st.error("No concepts found in the document. The text might be too short or need preprocessing.")
        return None
        
    # Find root node (most connected concept)
    try:
        root_node = max(concept_connections.items(), key=lambda x: x[1])[0]
    except ValueError:
        # If no connections, just take the first concept
        root_node = next(iter(significant_concepts))
    
    # Calculate levels based on connection distance from root
    levels = {root_node: 0}
    current_level = [root_node]
    visited = {root_node}
    max_level = 0
    
    # Process remaining concepts
    remaining_concepts = significant_concepts - {root_node}
    
    while current_level and remaining_concepts:
        next_level = []
        for node in current_level:
            # Find connected nodes
            for (source, target), _ in edge_weights.items():
                neighbor = target if source == node else source if target == node else None
                if neighbor and neighbor in remaining_concepts:
                    levels[neighbor] = levels[node] + 1
                    max_level = max(max_level, levels[neighbor])
                    next_level.append(neighbor)
                    visited.add(neighbor)
                    remaining_concepts.remove(neighbor)
        current_level = next_level
    
    # Handle any unconnected nodes by putting them in a new level
    if remaining_concepts:
        for concept in remaining_concepts:
            levels[concept] = max_level + 1
    
    # Add nodes for significant concepts
    for concept in significant_concepts:
        # Get concept description
        description = get_concept_description(llm, concept, all_text)
        
        # Calculate node size based on connections
        max_connections = max(concept_connections.values()) if concept_connections else 1
        connection_count = concept_connections.get(concept, 1)
        size = 25 * connection_count / max_connections if node_size else 25
        
        # Find direct relationships for this concept
        related_concepts = []
        for (source, target), weight in edge_weights.items():
            if source == concept and target in significant_concepts:
                related_concepts.append(target)
            elif target == concept and source in significant_concepts:
                related_concepts.append(source)
        
        # Calculate connection strength
        connection_strength = len(related_concepts)
        
        # Create enhanced tooltip with plain text formatting
        tooltip_lines = [
            f"=== {concept.title()} ===",
            "",
            description,
            "",
            f"Connections: {connection_strength} related concepts"
        ]
        
        if related_concepts:
            related_text = ", ".join(related_concepts[:5])
            if len(related_concepts) > 5:
                related_text += "..."
            tooltip_lines.append(f"Related to: {related_text}")
        
        tooltip = "\n".join(tooltip_lines)
        
        # Determine node color based on connection strength
        if theme == "dark":
            node_color_hex = f"#{min(128 + connection_strength * 20, 255):02x}7f7f"
        else:
            node_color_hex = f"#0000{min(128 + connection_strength * 20, 255):02x}"
        
        # Node properties
        node_props = {
            "label": concept.title(),  # Capitalize concept name
            "title": tooltip,
            "size": size,
            "color": node_color_hex,
            "font": {
                'size': int(10 + size/3),
                'bold': connection_strength > 5  # Bold text for highly connected nodes
            },
            "level": levels.get(concept, 0),  # Default to top level if not assigned
        }
        
        # Add the node
        net.add_node(concept, **node_props)
    
    # Add edges between significant concepts
    for (source, target), weight in edge_weights.items():
        if source in significant_concepts and target in significant_concepts:
            net.add_edge(
                source, target,
                value=weight,
                width=1 + weight,
                smooth={'type': 'vertical', 'forceDirection': 'vertical'},
                color={'color': edge_color}
            )
    
    # Configure visualization options for hierarchical layout
    net.set_options("""
    const options = {
        "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "opacity": 0.9,
            "font": {
                "size": 16,
                "face": "arial"
            },
            "shape": "box",
            "shadow": true
        },
        "edges": {
            "smooth": {
                "type": "cubicBezier",
                "forceDirection": "vertical",
                "roundness": 0.4
            },
            "shadow": true
        },
        "physics": {
            "enabled": true,
            "hierarchicalRepulsion": {
                "centralGravity": 0.5,
                "springLength": 100,
                "springConstant": 0.01,
                "nodeDistance": 120,
                "damping": 0.09
            },
            "solver": "hierarchicalRepulsion",
            "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 25
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "hideEdgesOnDrag": true,
            "multiselect": true,
            "tooltip": {
                "delay": 100,
                "fontSize": 14,
                "color": {
                    "background": "#ffffff",
                    "border": "#666666"
                }
            }
        },
        "layout": {
            "hierarchical": {
                "enabled": true,
                "levelSeparation": 150,
                "nodeSpacing": 150,
                "treeSpacing": 200,
                "direction": "UD",
                "sortMethod": "directed"
            }
        }
    }
    """)
    
    # Generate HTML file for interactive visualization
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w+') as f:
        net.write_html(f.name)
        return f.name

def display_memory_map(html_path: str):
    """Display the memory map in Streamlit."""
    if html_path is None:
        return
        
    try:
        # Read and display HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_string = f.read()
        components.html(html_string, height=600)
    except Exception as e:
        st.error(f"Error displaying memory map: {str(e)}")

def get_related_concepts(concept: str, documents: List[dict], window_size: int = 100) -> List[str]:
    """Get related content for a specific concept."""
    related_content = []
    
    for doc in documents:
        text = doc.page_content.lower()
        concept_positions = [m.start() for m in re.finditer(concept.lower(), text)]
        
        for pos in concept_positions:
            # Extract surrounding context
            start = max(0, pos - window_size)
            end = min(len(text), pos + len(concept) + window_size)
            context = text[start:end]
            
            if context:
                related_content.append(context)
    
    return related_content