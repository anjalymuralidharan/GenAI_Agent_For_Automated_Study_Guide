# Automated Study Guide Generator with RAG and LLMs

## Overview
This project implements an advanced Retrieval-Augmented Generation (RAG) system that creates interactive study guides using Ollama and the DeepSeek-r1 model. The system combines modern LLM technologies with efficient document processing to provide a comprehensive learning experience, including flashcards and mind maps.

### Key Features
- **RAG-based Document Processing**: Utilizes LangChain's LCEL (LangChain Expression Language) for efficient document retrieval and generation
- **Persistent Vector Storage**: Implements ChromaDB for reliable document vectorization and retrieval
- **Interactive UI**: Built with Streamlit for a user-friendly learning interface
- **Local LLM Integration**: Powered by Ollama with DeepSeek-r1 model for high-quality responses
- **Real-time Response Streaming**: Features token-by-token output streaming for immediate feedback
- **Dynamic Flashcards**: Generate and review AI-created flashcards for effective learning
- **Interactive Mind Maps**: Visualize concepts and their relationships through automated mind map generation


## Technical Architecture

### RAG Implementation
The project implements two approaches for RAG:
1. **LCEL Pipeline** (Modern Approach):
   ```python
   chain = retriever | prompt | llm | OutputParser
   ```
   - Provides smooth output streaming
   - Integrates seamlessly with Streamlit's write_stream method
   - Enhanced composability and maintainability

2. **Traditional LangChain Chain** (Legacy Support):
   - Implements RetrievalQA for backwards compatibility
   - Supports terminal-based output streaming via callbacks

![LCEL Pipeline Flow](./assets/lcel_pipe_flow.png)

### Advanced Learning Features

#### Flashcard System
- Automated generation of question-answer pairs from documents
- Spaced repetition support for optimal learning
- Interactive review interface with performance tracking
- Customizable difficulty levels and topics

#### Mind Map Generation
- Automatic concept extraction and relationship mapping
- Interactive visualization using vis.js network graphs
- Hierarchical knowledge representation
- Dynamic node expansion and exploration

### Vector Store Implementation
- Uses ChromaDB for persistent vector storage
- Automatically processes PDF files from the `data_source` directory
- Maintains efficient retrieval for context-aware responses


## Project Structure
```
├── data_source/         # Sample PDF documents
├── lib/                 # External libraries and utilities
├── src/
│   ├── data_loader.py  # Document processing utilities
│   ├── flash_card.py   # Flashcard generation logic
│   ├── memory_map.py   # Memory management
│   ├── rag_chain.py    # RAG chain implementation
│   ├── vectorstore.py  # Vector store operations
│   └── templates/      # Template files for Q&A
├── rag.py              # Main RAG implementation
└── st_app.py          # Streamlit application
```

## Installation Guide

### 1. Repository Setup
```shell
git clone https://github.com/anjalymuralidharan/GenAI_Agent_For_Automated_Study_Guide
cd GenAI_Agent_For_Automated_Study_Guide
```

### 2. Virtual Environment Setup
```shell
# Using venv
python3 -m venv .venv
source .venv/bin/activate  # For Unix/MacOS
# OR
.venv\Scripts\activate     # For Windows

# Using conda
conda create -n study_guide_env python=3.9
conda activate study_guide_env
```

### 3. Core Dependencies
Install the primary project dependencies:
```shell
pip install -r requirements.txt
```

### 4. Ollama Setup

1. **Install Ollama**:
   - Visit [Ollama's official website](https://ollama.ai) to download and install Ollama for your operating system
   - Follow the installation instructions for your platform

2. **Setup DeepSeek-r1 Model**:
   ```shell
   ollama pull deepseek-r1:latest
   ```

   This will download and set up the DeepSeek-r1 model in Ollama.


## Usage

### Starting the Application
```shell
streamlit run st_app.py
```

### Using the Interface

1. **Document Processing**:
   - Upload PDF documents to the `data_source` directory
   - The system will automatically process and vectorize the content

2. **Interactive Learning**:
   - Launch the application using Streamlit
   - Use the chat interface for general questions
   - Generate flashcards from your documents
   - Create and explore mind maps of concepts

3. **Flashcard Features**:
   - Auto-generate flashcards from uploaded content
   - Review cards with spaced repetition
   - Track learning progress
   - Filter cards by topic or difficulty

4. **Mind Map Usage**:
   - View automatically generated concept maps
   - Click nodes to expand relationships
   - Explore connected concepts
   - Export mind maps for external use

## Performance Optimization

### System Requirements
- Ollama runs locally on your machine
- DeepSeek-r1 model requires approximately 8GB RAM
- SSD recommended for faster vector store operations

### Best Practices
- Keep PDF documents well-structured for better processing
- Use clear, specific questions for better responses
- Regularly review and update flashcards
- Explore mind map connections for comprehensive understanding

## Contributing
Contributions are welcome! Please feel free to submit pull requests, create issues, or suggest improvements.



    
 
