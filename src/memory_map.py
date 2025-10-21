from typing import List, Dict, Any
import streamlit as st
from streamlit_markmap import markmap
from langchain_ollama import OllamaLLM
from langchain_core.vectorstores import VectorStore
from langchain_core.prompts import PromptTemplate

def generate_topic_hierarchy(text: str, llm: OllamaLLM) -> str:
    """Generate a hierarchical topic structure using LLM."""
    
    # First, get the main topic and summary
    main_topic_prompt = PromptTemplate.from_template("""
    Analyze this text and identify the main topic and a brief summary.
    Response should be in this exact format:
    # Main Topic Name Here
    - Brief summary of the main topic (max 100 chars)

    Text to analyze:
    {text}
    """)

    subtopics_prompt = PromptTemplate.from_template("""
    Based on this text, generate a hierarchical outline of the key topics and subtopics.
    Use exactly this format with proper indentation:

    ## Key Topic 1
    - Brief description
    
    ### Subtopic 1.1
    - Key point 1
    - Key point 2
    
    ### Subtopic 1.2
    - Key point 1
    - Key point 2
    
    ## Key Topic 2
    - Brief description
    
    ### Subtopic 2.1
    - Key point 1
    - Key point 2

    Important:
    - Generate 3-5 key topics
    - Each key topic should have 2-3 subtopics
    - Keep descriptions short and clear
    - Use bullet points for details
    - No other formatting or text

    Text to analyze:
    {text}
    """)

    try:
        # Get main topic
        main_topic_response = llm.invoke(main_topic_prompt.format(text=text[:3000]))  # Use first part for main topic
        
        # Get subtopics structure
        subtopics_response = llm.invoke(subtopics_prompt.format(text=text))
        
        # Combine and clean up the responses
        full_content = main_topic_response + "\n\n" + subtopics_response
        
        # Clean up the response
        cleaned_content = (
            full_content.strip('`')
            .replace('```markdown', '')
            .replace('```', '')
            .strip()
        )
        
        # Verify structure
        lines = cleaned_content.split('\n')
        if not any(line.startswith('# ') for line in lines):
            raise ValueError("Missing main topic heading")
        if not any(line.startswith('## ') for line in lines):
            raise ValueError("Missing subtopics")
            
        return cleaned_content
            
    except Exception as e:
        st.error(f"Error generating topic hierarchy: {str(e)}")
        return None

def format_markmap(content: str) -> str:
    """Format the markdown content for markmap visualization."""
    
    # Define markmap configuration
    header = """---
markmap:
  colorFreezeLevel: 1
  maxWidth: 500
  initialExpandLevel: 2
  zoom: true
  pan: true
  color:
    - "#2196F3"  # Main topic (blue)
    - "#4CAF50"  # Key topics (green)
    - "#FF9800"  # Subtopics (orange)
  style:
    nodeText:
      padding: 4px
      fontSize: 14px
      fontWeight: normal
---

"""
    try:
        # Clean up the content
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Ensure proper spacing for list items
            if line.startswith('- '):
                # If this is a bullet point, ensure it's properly indented based on previous line
                prev_line = cleaned_lines[-1] if cleaned_lines else ""
                if prev_line.startswith('#'):
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append("  " + line)  # Add indentation for better hierarchy
            else:
                cleaned_lines.append(line)
        
        # Join lines with proper spacing
        cleaned_content = '\n'.join(cleaned_lines)
        
        return header + cleaned_content
        
    except Exception as e:
        st.error(f"Error formatting markmap: {str(e)}")
        return content  # Return original content if formatting fails

def create_memory_map(documents: List[dict], vectorstore: VectorStore = None, height: int = 600) -> None:
    """
    Create and display an interactive mind map visualization using markmap.
    
    Args:
        documents: List of document chunks
        vectorstore: Vector store containing the document embeddings (optional)
        height: Height of the visualization in pixels
    """
    try:
        with st.spinner("Generating mind map from documents..."):
            # Initialize progress tracking
            progress = st.progress(0)
            status = st.empty()
            
            # Combine document contents with proper chunking
            text_chunks = []
            total_length = 0
            max_chunk_size = 4000  # Maximum size for LLM processing
            
            for doc in documents:
                content = doc.page_content.strip()
                if total_length + len(content) < max_chunk_size:
                    text_chunks.append(content)
                    total_length += len(content)
            
            all_text = " ".join(text_chunks)
            progress.progress(10)
            
            # Initialize LLM with specific parameters
            status.text("Initializing language model...")
            llm = OllamaLLM(
                model="deepseek-r1",
                temperature=0.3,  # Lower temperature for more focused output
                max_tokens=2000   # Ensure enough tokens for full response
            )
            progress.progress(20)
            
            # Generate markdown content
            status.text("Analyzing document content...")
            markdown_content = generate_topic_hierarchy(all_text, llm)
            progress.progress(60)
            
            if markdown_content:
                # Format for markmap
                status.text("Creating visualization...")
                markmap_data = format_markmap(markdown_content)
                progress.progress(90)
                
                # Create container for mind map
                map_container = st.container()
                with map_container:
                    # Display the mind map with error handling
                    try:
                        markmap(markmap_data, height=height)
                        progress.progress(100)
                        status.empty()
                        
                        # Display usage instructions
                        st.success("✅ Mind map generated successfully!")
                        st.markdown("""
                        ### 🎮 How to Use the Mind Map
                        - 👆 Click topics to expand/collapse
                        - 🔍 Use mouse wheel to zoom in/out
                        - 🖐️ Drag to pan around
                        - 📍 Double-click to focus on a topic
                        
                        ### 📝 Mind Map Structure
                        - Main topic at the center
                        - Key topics as primary branches
                        - Subtopics and details as secondary branches
                        - Click any node to explore related concepts
                        """)
                        
                    except Exception as viz_error:
                        st.error(f"Error displaying mind map: {str(viz_error)}")
                        st.code(markmap_data, language="markdown")
                        
            else:
                st.error("❌ Could not generate mind map. Please try with a smaller document or different content.")
                st.info("Try uploading a smaller document or using the regenerate button.")
                
    except Exception as e:
        st.error(f"❌ Error generating mind map: {str(e)}")
        st.info("💡 Try reducing the document size or complexity if the error persists.")