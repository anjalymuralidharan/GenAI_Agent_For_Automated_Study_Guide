from langchain.chains import RetrievalQA
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

DEFAULT_PROMPT_TEMPLATE = """
You are a highly knowledgeable assistant designed to answer questions based on extracted content from PDF documents. Your goal is to provide accurate, detailed, and easy-to-understand answers using only the provided context.

Your response must:
1. Be thorough and relevant to the provided context
2. Use direct quotes or references from the context when appropriate
3. Clarify complex or technical terms in simple language when needed
4. Organize your response using bullet points, numbered lists, or clear headings if multiple ideas are involved
5. Avoid assuming facts that are not in the context—even if they seem obvious
6. Maintain a formal and informative tone suitable for academic, business, or technical users
7. Correctly interpret tables, diagrams, or OCR text when present in the context
8. Ignore unrelated or noisy data often found in PDFs (e.g. headers, footers, page numbers)

Context:
{context}

Question:
{question}

Detailed Answer (provide a thorough explanation using only the information from the context):
"""

def create_rag_chain(retriever, prompt_template=DEFAULT_PROMPT_TEMPLATE, model_name="deepseek-r1"):
    """Create a RAG chain using the provided retriever and prompt template."""
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=['context', 'question']
    )

    llm = OllamaLLM(model=model_name)

    # Create the RAG chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()} |
        prompt | llm | StrOutputParser()
    )

    return rag_chain

def create_qa_chain(retriever, prompt_template=DEFAULT_PROMPT_TEMPLATE, model_name="deepseek-r1"):
    """Create a RetrievalQA chain using the provided retriever and prompt template."""
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=['context', 'question']
    )

    llm = OllamaLLM(model=model_name)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        chain_type_kwargs={'prompt': prompt},
        verbose=False
    )

    return qa_chain

def format_docs(docs):
    """Format documents for RAG context."""
    return "\n\n".join([doc.page_content for doc in docs])