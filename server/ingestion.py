from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_db", 
)

def load_pdfs(file_paths_with_urls):
    """
    Load and return documents from a list of PDF file paths with their source URLs.
    Args:
        file_paths_with_urls (dict): Dictionary mapping file paths to their source URLs.
    Returns:
        list: List of loaded documents.
    """
    all_docs = []
    for file_path, source_url in file_paths_with_urls.items():
        loader = PyMuPDFLoader(file_path, mode='page')
        docs = loader.load()
        # Add source URL to metadata
        for doc in docs:
            doc.metadata['source_url'] = source_url
        all_docs.extend(docs)
    return all_docs

def ingest_pdfs(file_paths_with_urls):
    """
    Add data to the vector store from a dictionary of PDF file paths with their source URLs.
    
    :param file_paths_with_urls: Dictionary mapping file paths to their source URLs
    """

    docs = load_pdfs(file_paths_with_urls)

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size= 250,
        chunk_overlap = 50
    )

    docs_splits = text_splitter.split_documents(docs)

    vector_store.add_documents(docs_splits)
    return len(docs_splits)




    
