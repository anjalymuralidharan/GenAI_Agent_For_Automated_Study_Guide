import os
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

def setup_vectorstore(documents, persist_directory="./vector_stores", collection_name="chroma1"):
    """Set up and configure the vector store."""
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)

    # Default embedding model that supports embeddings via Ollama
    embed_model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    embeddings = OllamaEmbeddings(model=embed_model)

    # Create new vectorstore from documents
    vectordb = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=collection_name
    )
    vectordb.persist()

    return vectordb

def load_vectorstore(persist_directory="./vector_stores", collection_name="chroma1"):
    """Load an existing vector store from disk."""
    embed_model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    embeddings = OllamaEmbeddings(model=embed_model)
    
    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=collection_name
    )
    return vectordb