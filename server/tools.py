from langchain.tools import tool
from ingestion import vector_store

retriever = vector_store.as_retriever()



@tool
def retrive_documents(query: str) -> str:
    """
    Retrieve relevant documents based on the query.
    
    Args:
        query (str): The search query.
        
    Returns:
        str: Retrieved documents as a string.
    """
    docs = retriever.invoke(query)

    # combine documents with metadata

    retrived_content = ""

    for doc in docs:
        retrived_content += f"Document Content: \n {doc.page_content}\n\n Metadata:\n page: {doc.metadata.get('page','N/A')} \n source: {doc.metadata.get('source','N/A')}"

    return retrived_content

retriever_tool = retrive_documents
    