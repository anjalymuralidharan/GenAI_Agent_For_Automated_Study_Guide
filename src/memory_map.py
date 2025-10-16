from typing import List, Dict
import spacy
import streamlit as st
from streamlit_markmap import markmap
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

def extract_concepts_and_relations(text: str) -> Dict[str, List[str]]:
    """Extract key concepts and their relationships from text."""
    doc = nlp(text)
    
    # Create a hierarchical structure
    concept_hierarchy = {}
    
    # Process each sentence
    for sent in doc.sents:
        # Get main subject of the sentence (usually the first noun chunk)
        subjects = [chunk for chunk in sent.noun_chunks]
        if subjects:
            main_subject = subjects[0].text.strip().lower()
            # Get related concepts from the same sentence
            related = [chunk.text.strip().lower() for chunk in subjects[1:]]
            
            # Add to hierarchy
            if main_subject not in concept_hierarchy:
                concept_hierarchy[main_subject] = []
            concept_hierarchy[main_subject].extend(related)
    
    return concept_hierarchy

def get_concept_description(llm: OllamaLLM, concept: str, context: str) -> str:
    """Use LLM to generate a concise bullet-point description for a concept."""
    prompt = f"""Analyze the concept "{concept}" and provide exactly 2-3 key points in this format:

    • [First key point - max 50 chars]
    • [Second key point - max 50 chars]
    • [Optional third point - max 50 chars]

    Context: {context}

    STRICT REQUIREMENTS:
    - Provide ONLY 2-3 bullet points, no more
    - Each point must be under 50 characters
    - Use clear, memorable language
    - Focus on the most important aspects
    - Start each point with an action verb
    - NO introduction or additional text
    """
    
    try:
        result = llm.invoke(prompt)
        # Clean and format the response
        points = [line.strip() for line in result.split('\n') if line.strip().startswith('•')]
        points = points[:3]  # Ensure max 3 points
        formatted_points = []
        for point in points:
            point = point.strip('• ').strip()
            if len(point) > 50:  # Truncate if too long
                point = point[:47] + "..."
            formatted_points.append(f"• {point}")
        return "\n".join(formatted_points) if formatted_points else f"• Key point about {concept}"
    except:
        return f"• Key point about {concept}"

def create_markmap_content(documents: List[dict], min_concepts: int = 5) -> str:
    """
    Create a markmap-compatible markdown structure from document concepts.
    """
    # Combine all document contents
    all_text = " ".join([doc.page_content for doc in documents])
    
    # Extract concepts and relations
    concept_hierarchy = extract_concepts_and_relations(all_text)
    
    # Initialize LLM
    llm = OllamaLLM(model="deepseek-r1")
    
    # Create markmap markdown content
    markdown_content = [
        "---",
        "markmap:",
        "  colorFreezeLevel: 2",
        "---",
        "",
        "# Document Concept Map",
        ""
    ]
    
    # Process main concepts
    for main_concept, related_concepts in concept_hierarchy.items():
        # Get concept description
        description = get_concept_description(llm, main_concept, all_text)
        
        # Add main concept with description
        markdown_content.extend([
            f"## {main_concept.title()}",
            f"- {description}"
        ])
        
        # Add related concepts
        if related_concepts:
            markdown_content.append("### Related Concepts")
            for related in set(related_concepts):
                rel_description = get_concept_description(llm, related, all_text)
                markdown_content.append(f"- {related.title()}: {rel_description}")
        
        markdown_content.append("")
    
    return "\n".join(markdown_content)

def create_memory_map(documents: List[dict], height: int = 600) -> None:
    """
    Create and display an interactive mind map visualization using markmap.
    
    Args:
        documents: List of document chunks
        height: Height of the visualization in pixels
    """
    # Generate markmap content
    markmap_data = create_markmap_content(documents)
    
    # Display the mind map
    markmap(markmap_data, height=height)