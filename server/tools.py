from langchain.tools import tool
from services import get_vector_store
import os
import re

_vector_store = None

# Tax acronyms mapping for query expansion
TAX_ACRONYMS = {
    "SET": "Statement of Estimated Tax Payable",
    "VAT": "Value Added Tax",
    "PAYE": "Pay As You Earn",
    "WHT": "Withholding Tax",
    "APIT": "Advanced Personal Income Tax",
    "ESC": "Economic Service Charge",
    "NBT": "Nation Building Tax",
    "SVAT": "Simplified Value Added Tax",
    "TIN": "Tax Identification Number",
    "CIT": "Corporate Income Tax",
    "PIT": "Personal Income Tax",
    "IRD": "Inland Revenue Department",
}

def expand_query_acronyms(query: str) -> str:
    """Expand tax acronyms in the query for better retrieval."""
    expanded_query = query
    
    # Find uppercase words that might be acronyms (2-5 chars)
    for acronym, full_form in TAX_ACRONYMS.items():
        # Match the acronym as a whole word (case-sensitive for uppercase)
        pattern = r'\b' + acronym + r'\b'
        if re.search(pattern, query):
            # Replace with "full_form (ACRONYM)" for better matching
            expanded_query = re.sub(pattern, f"{full_form} ({acronym})", expanded_query)
    
    return expanded_query

def get_retriever():
    global _vector_store
    if _vector_store is None:
        _vector_store = get_vector_store()
    return _vector_store.store.as_retriever(search_kwargs={"k": 6})



@tool
def retrive_documents(query: str) -> str:
    """
    Retrieve relevant documents based on the query.
    
    Args:
        query (str): The search query.
        
    Returns:
        str: Retrieved documents as a string.
    """
    # Expand acronyms in query for better retrieval
    expanded_query = expand_query_acronyms(query)
    print(f"[Retriever] Original query: {query}")
    print(f"[Retriever] Expanded query: {expanded_query}")
    
    retriever = get_retriever()
    docs = retriever.invoke(expanded_query)

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
    