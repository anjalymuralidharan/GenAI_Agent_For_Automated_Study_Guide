import os
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_pdf_files(files: List[bytes], filenames: List[str]) -> list:
    """Load documents from uploaded PDF files."""
    documents = []
    
    # Create a temporary directory for storing uploaded files
    temp_dir = "./temp_uploads"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        # Save and process each uploaded file
        for file_content, filename in zip(files, filenames):
            temp_path = os.path.join(temp_dir, filename)
            
            # Save the uploaded file temporarily
            with open(temp_path, 'wb') as f:
                f.write(file_content)
            
            # Load the PDF
            loader = PyPDFLoader(temp_path)
            documents.extend(loader.load())
            
            # Clean up the temporary file
            os.remove(temp_path)
            
    finally:
        # Ensure temp directory is cleaned up
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except:
                pass
                
    return documents

def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Split documents into chunks using RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_documents(documents)

def format_docs(docs):
    """Format documents for RAG context."""
    return "\n\n".join([doc.page_content for doc in docs])