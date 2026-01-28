from abc import ABC, abstractmethod
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List
from interfaces import DocumentLoader, TextSplitter, VectorStore
from dotenv import load_dotenv

class DocumentLoaderFactory:
    @staticmethod
    def create_loader(file_type: str) -> DocumentLoader:
        loaders = {
            'pdf': PDFDocumentLoader,
        }
        loader_class = loaders.get(file_type.lower())
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_type}")
        return loader_class()

class TextSplitterFactory:
    @staticmethod
    def create_splitter(splitter_type: str = "tiktoken", chunk_size: int = 250, chunk_overlap: int = 50) -> TextSplitter:
        if splitter_type == "tiktoken":
            return TikTokenTextSplitter(chunk_size, chunk_overlap)
        raise ValueError(f"Unsupported splitter type: {splitter_type}")

class VectorStoreFactory:
    @staticmethod
    def create_vector_store(store_type: str, collection_name: str, persist_directory: str) -> VectorStore:
        if store_type == "chroma":
            return ChromaVectorStore(collection_name, persist_directory)
        raise ValueError(f"Unsupported vector store type: {store_type}")

class EmbeddingFactory:
    @staticmethod
    def create_embedding(provider: str, model: str):
        load_dotenv()
        if provider == "google":
            return GoogleGenerativeAIEmbeddings(model=model)
        raise ValueError(f"Unsupported embedding provider: {provider}")

class PDFDocumentLoader(DocumentLoader):
    def load(self, file_path: str, source_url: str) -> List:
        loader = PyMuPDFLoader(file_path, mode='page')
        docs = loader.load()
        for doc in docs:
            doc.metadata['source_url'] = source_url
        return docs

class TikTokenTextSplitter(TextSplitter):
    def __init__(self, chunk_size: int = 250, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def split_documents(self, documents: List) -> List:
        return self.splitter.split_documents(documents)

class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str, persist_directory: str):
        embeddings = EmbeddingFactory.create_embedding("google", "models/gemini-embedding-001")
        self.store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory
        )
    
    def add_documents(self, documents: List) -> None:
        self.store.add_documents(documents)
