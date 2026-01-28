from langchain.tools import tool
from ingestion import vector_store
import os

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
        # Extract clean document name (remove path and extension)
        source = doc.metadata.get('source', 'N/A')
        source_url = doc.metadata.get('source_url', '')
        if source != 'N/A':
            # Get filename without path and remove extension
            source = os.path.splitext(os.path.basename(source))[0]
        
        retrived_content += f"Document Content: \n {doc.page_content}\n\n Metadata:\n page: {doc.metadata.get('page','N/A')} \n source: {source} \n source_url: {source_url}\n\n"

    return retrived_content

retriever_tool = retrive_documents
    