from langchain.tools import tool
from services import get_vector_store
import os

_vector_store = None

def get_retriever():
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store.store.as_retriever()



@tool
def retrive_documents(query: str) -> str:
    """
    Retrieve relevant documents based on the query.
    
    Args:
        query (str): The search query.
        
    Returns:
        str: Retrieved documents as a string.
    """
    retriever = get_retriever()
    docs = retriever.invoke(query)

    # combine documents with metadata

    retrived_content = ""

    for doc in docs:
        source = doc.metadata.get('source', 'N/A')
        source_url = doc.metadata.get('source_url', '')
        page_num = doc.metadata.get('page', 'N/A')
        
        if source != 'N/A':
            source = os.path.splitext(os.path.basename(source))[0]
        
        if page_num != 'N/A' and isinstance(page_num, int):
            page_num = page_num + 1
        
        retrived_content += f"Document Content: \n {doc.page_content}\n\n Metadata:\n page: {page_num} \n source: {source} \n source_url: {source_url}\n\n"

    return retrived_content

retriever_tool = retrive_documents
    