from langchain.chains import RetrievalQA
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

DEFAULT_PROMPT_TEMPLATE = """Based on the following context, provide a comprehensive and detailed answer to the question. Your response should:

1. Be thorough and informative while remaining relevant
2. Include specific examples or quotes from the context when applicable
3. Break down complex concepts into clear explanations
4. Use bullet points or numbered lists for multiple points
5. Provide explanations at an appropriate level of detail based on the question's complexity

Context:
{context}

Question: {question}

Detailed Answer (provide a thorough explanation with examples and clarification where needed):"""

def create_rag_chain(retriever, prompt_template=DEFAULT_PROMPT_TEMPLATE, model_name="gemma3"):
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

def create_qa_chain(retriever, prompt_template=DEFAULT_PROMPT_TEMPLATE, model_name="gemma3"):
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