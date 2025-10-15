import os
import random
import streamlit as st
from src.data_loader import load_pdf_files, split_documents
from src.vectorstore import setup_vectorstore, load_vectorstore
from src.rag_chain import create_rag_chain
from src.memory_map import (
    create_memory_map, display_memory_map, get_related_concepts,
    extract_concepts_and_relations
)
from src.flash_card import FlashcardGenerator
from langchain_ollama import OllamaLLM

# Set environment variable to disable telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Configure the Streamlit page
st.set_page_config(
    page_title="PDF Learning Assistant",
    page_icon=':books:',
    layout="wide"
)

# Custom CSS to improve chat layout
st.markdown("""
<style>
    /* Chat container styling */
    .stChatFloatingInputContainer {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 800px !important;
        max-width: calc(100% - 500px) !important;
        padding: 20px !important;
        z-index: 1000 !important;
        background: linear-gradient(180deg, transparent 0%, rgba(255,255,255,0.9) 20%) !important;
    }
    
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        padding: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }
    
    /* Add padding to main content to prevent overlap with input */
    .main > div {
        padding-bottom: 120px !important;
        margin-bottom: 0 !important;
    }
    
    /* Chat input styling */
    .stChatInput {
        border-radius: 10px !important;
    }
    
    /* Message styling */
    .stChatMessage {
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation
with st.sidebar:
    st.title("Navigation")
    selected_page = st.radio(
        "Choose a feature:",
        ["PDF Chat", "Flashcards", "Memory Map"],
        key="navigation"
    )
    
    # File upload in sidebar - available for all features
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload your PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more PDF files to work with"
    )

# Main content area
if selected_page == "PDF Chat":
    st.title("💬 Chat with your PDFs")
elif selected_page == "Flashcards":
    st.title("🗂 Flashcards")
    st.info("🚧 Flashcards feature coming soon! This will help you create and review flashcards from your PDF content.")
elif selected_page == "Memory Map":
    st.title("🗺 Memory Map")
    st.info("🚧 Memory Map feature coming soon! This will help you visualize connections between concepts in your documents.")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'files_processed' not in st.session_state:
    st.session_state.files_processed = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "PDF Chat"
    
# Initialize flashcard-related session state
if 'qa_dict' not in st.session_state:
    st.session_state.qa_dict = {}
if 'idx' not in st.session_state:
    st.session_state.idx = 0
if 'show_front' not in st.session_state:
    st.session_state.show_front = True
if 'generator' not in st.session_state:
    st.session_state.generator = FlashcardGenerator()
if 'flashcards_generated' not in st.session_state:
    st.session_state.flashcards_generated = False

# Process uploaded files
if uploaded_files and not st.session_state.files_processed:
    with st.spinner("Processing PDF files..."):
        # Convert uploaded files to format needed by load_pdf_files
        files_content = [file.read() for file in uploaded_files]
        files_names = [file.name for file in uploaded_files]
        
        # Load and process documents
        documents = load_pdf_files(files_content, files_names)
        chunks = split_documents(documents)
        
        # Create new vectorstore
        st.session_state.vectorstore = setup_vectorstore(chunks)
        st.session_state.files_processed = True
        st.sidebar.success(f"✅ Successfully processed {len(uploaded_files)} PDF files")

# Display appropriate content based on selection
if selected_page == "PDF Chat":
    if st.session_state.files_processed:
        # Create a two-row layout
        chat_area = st.container()
        input_area = st.container()
        
        # Reserve space for input at bottom
        with input_area:
            st.write("")  # Add some spacing
            prompt = st.chat_input("Ask a question about your PDFs...", key="chat_input")
        
        # Display chat messages in the chat area
        with chat_area:
            # Add some padding at the top
            st.write("")
            
            # Create a scrollable container for messages
            with st.container():
                # Display chat messages
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

            if prompt:
                # Add user message to chat
                st.session_state.messages.append({'role': 'user', 'content': prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Create retriever and RAG chain
                retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 4})  # Increased context
                rag_chain = create_rag_chain(retriever)

                # Generate and stream response
                with st.spinner("Thinking..."):
                    with st.chat_message('assistant'):
                        response_placeholder = st.empty()
                        full_response = ""
                        
                        # Stream the response
                        for piece in rag_chain.stream(prompt):
                            full_response += piece
                            response_placeholder.markdown(full_response + "▌")
                        response_placeholder.markdown(full_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({'role': 'assistant', 'content': full_response})
                
                # Scroll to bottom (this is handled automatically by Streamlit)
    else:
        st.info("� Please upload some PDF files in the sidebar to start chatting!")

elif selected_page == "Flashcards":
    if st.session_state.files_processed:
        st.title("🗂️ Flashcards")
        
        # Add controls in sidebar
        with st.sidebar:
            st.markdown("### 📑 Flashcard Controls")
            num_cards = st.slider("Number of flashcards to generate", 
                                min_value=3, max_value=20, value=5)
            
            if not st.session_state.flashcards_generated:
                if st.button("🎲 Generate New Flashcards"):
                    with st.spinner("Generating flashcards from your documents..."):
                        # Initialize LLM
                        llm = OllamaLLM(model="gemma3")
                        
                        # Get all text from documents
                        retriever = st.session_state.vectorstore.as_retriever()
                        docs = retriever.get_relevant_documents("")
                        all_text = " ".join([doc.page_content for doc in docs])
                        
                        # Generate questions prompt
                        gen_questions_prompt = f"""Generate {num_cards} high-quality flashcard questions and answers from the given text. Follow these guidelines:

                        1. Question Types (mix evenly):
                           - Definitions: "What is X?"
                           - Concepts: "How does X work?"
                           - Applications: "Why is X important?"
                           - Relationships: "How are X and Y related?"
                        
                        2. Answer Guidelines:
                           - Clear and concise (2-3 sentences)
                           - Focus on key information
                           - Include specific examples when relevant
                        
                        3. Format each QA pair exactly like this, one per line:
                        {{"question": "What is X?", "answer": "X is Y and does Z. It is important because W."}}

                        Text to analyze: {all_text}

                        Generate exactly {num_cards} question-answer pairs, one per line:"""
                        
                        # Get response and parse QA pairs
                        response = llm.invoke(gen_questions_prompt)
                        
                        # Extract QA pairs from response
                        qa_pairs = {}
                        try:
                            import json
                            import re

                            # Find all JSON objects in the response using regex
                            json_pattern = r'{[^}]+}'
                            json_matches = re.finditer(json_pattern, response)
                            
                            for match in json_matches:
                                try:
                                    json_str = match.group()
                                    # Replace any escaped quotes and normalize whitespace
                                    json_str = json_str.replace('\\"', '"').strip()
                                    
                                    qa = json.loads(json_str)
                                    if ('question' in qa and 'answer' in qa and 
                                        isinstance(qa['question'], str) and 
                                        isinstance(qa['answer'], str) and
                                        len(qa['question'].strip()) > 0 and 
                                        len(qa['answer'].strip()) > 0):
                                        
                                        # Clean and format the QA pair
                                        question = qa['question'].strip()
                                        answer = qa['answer'].strip()
                                        if not question.endswith('?'):
                                            question += '?'
                                        
                                        qa_pairs[question] = answer
                                        
                                        if len(qa_pairs) >= num_cards:
                                            break
                                except json.JSONDecodeError:
                                    continue
                                
                            # If we didn't get enough QA pairs, try to generate more
                            if len(qa_pairs) < num_cards:
                                st.warning(f"Only generated {len(qa_pairs)} valid flashcards out of {num_cards} requested.")
                                
                        except Exception as e:
                            st.error(f"Error generating flashcards: {str(e)}")
                        
                        st.session_state.qa_dict = qa_pairs
                        st.session_state.flashcards_generated = True
                        st.session_state.idx = 0
                        st.session_state.show_front = True
                        st.rerun()
        
        # Main flashcard display
        if st.session_state.flashcards_generated and st.session_state.qa_dict:
            questions = list(st.session_state.qa_dict.keys())
            current_q = questions[st.session_state.idx]
            current_a = st.session_state.qa_dict[current_q]
            
            # Show progress
            st.markdown(
                f"<p style='text-align: center; color: #888;'>Card {st.session_state.idx + 1} of {len(questions)}</p>",
                unsafe_allow_html=True
            )
            
            # Generate and display current flashcard
            if st.session_state.show_front:
                front, _ = st.session_state.generator.create_flashcard_pair(current_q, current_a)
                st.image(front)
            else:
                _, back = st.session_state.generator.create_flashcard_pair(current_q, current_a)
                st.image(back)
            
            # Card controls
            col1, col2, col3, col4 = st.columns([1,1,1,1])
            
            with col1:
                if st.button("⬅️ Previous"):
                    st.session_state.idx = (st.session_state.idx - 1) % len(questions)
                    st.session_state.show_front = True
                    st.rerun()
            
            with col2:
                if st.button("🔄 Flip"):
                    st.session_state.show_front = not st.session_state.show_front
                    st.rerun()
            
            with col3:
                if st.button("➡️ Next"):
                    st.session_state.idx = (st.session_state.idx + 1) % len(questions)
                    st.session_state.show_front = True
                    st.rerun()
            
            with col4:
                if st.button("🔀 Random"):
                    st.session_state.idx = random.randint(0, len(questions) - 1)
                    st.session_state.show_front = True
                    st.rerun()
        
        elif not st.session_state.flashcards_generated:
            st.info("👈 Click 'Generate New Flashcards' in the sidebar to create flashcards from your documents!")
    else:
        st.info("👈 Please upload some PDF files in the sidebar to create flashcards!")

elif selected_page == "Memory Map":
    if st.session_state.files_processed:
        st.write("📚 Interactive Memory Map of Your Documents")
        
        # Add controls for visualization
        col1, col2 = st.columns([3, 1])
        with col2:
            st.markdown("### 🎨 Visualization Options")
            
            min_connections = st.slider(
                "Minimum Connections",
                min_value=0,
                max_value=10,
                value=1,
                help="Filter concepts by minimum number of connections"
            )
            
            theme = st.selectbox(
                "Color Theme",
                options=["light", "dark"],
                help="Choose the visualization theme"
            )
            
            node_size = st.checkbox(
                "Size nodes by connections",
                value=True,
                help="Make more connected nodes larger"
            )
            
            st.markdown("### 🎮 How to Use")
            st.markdown("""
            - 👆 Click nodes to see concept descriptions
            - 🔍 Scroll to zoom in/out
            - 🖐️ Drag background to pan
            - ✨ Double-click to focus on a node
            - ✨ Double-click to focus
            - 🎯 Hold to select multiple
            """)
        
        with col1:
            with st.spinner("Generating memory map..."):
                # Get documents from vectorstore
                retriever = st.session_state.vectorstore.as_retriever()
                docs = retriever.get_relevant_documents("")  # Get all documents
                
                # Create and display memory map with selected options
                content = create_memory_map(
                    docs,
                    min_connections=min_connections,
                    theme=theme,
                    node_size=node_size
                )
                display_memory_map(content)
        
        # Add concept explorer
        st.markdown("### 🔍 Concept Explorer")
        if 'selected_concept' not in st.session_state:
            st.session_state.selected_concept = None
            
        # Get all concepts for selection
        all_concepts = []
        with st.spinner("Loading concepts..."):
            for doc in docs:
                concepts, _ = extract_concepts_and_relations(doc.page_content)
                all_concepts.extend(concepts)
        all_concepts = sorted(list(set(all_concepts)))
        
        # Concept selector
        selected_concept = st.selectbox(
            "Select a concept to explore",
            options=all_concepts,
            index=None,
            placeholder="Choose a concept..."
        )
        
        if selected_concept:
            st.markdown(f"### Context for: {selected_concept}")
            related_content = get_related_concepts(selected_concept, docs)
            
            for i, context in enumerate(related_content, 1):
                with st.expander(f"Context {i}"):
                    st.markdown(context)
    else:
        st.info("👈 Please upload some PDF files in the sidebar to create a memory map!")

# Add reset functionality in sidebar
st.sidebar.markdown("---")
if st.session_state.files_processed or st.session_state.messages:
    def reset_all():
        st.session_state.messages = []
        st.session_state.files_processed = False
        st.session_state.vectorstore = None
        st.rerun()
    
    st.sidebar.button('Reset Everything', on_click=reset_all, help="Clear all uploaded files and chat history")
