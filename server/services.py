from pathlib import Path
import shutil
from typing import Dict, List
from interfaces import DocumentLoader, TextSplitter, VectorStore, FileManager
from factories import DocumentLoaderFactory, TextSplitterFactory, VectorStoreFactory

class DocumentIngestionService:
    def __init__(
        self,
        document_loader: DocumentLoader,
        text_splitter: TextSplitter,
        vector_store: VectorStore
    ):
        self.document_loader = document_loader
        self.text_splitter = text_splitter
        self.vector_store = vector_store
    
    def ingest_documents(self, file_paths_with_urls: Dict[str, str]) -> int:
        all_docs = []
        for file_path, source_url in file_paths_with_urls.items():
            docs = self.document_loader.load(file_path, source_url)
            all_docs.extend(docs)
        
        doc_splits = self.text_splitter.split_documents(all_docs)
        self.vector_store.add_documents(doc_splits)
        
        return len(doc_splits)

class LocalFileManager(FileManager):
    def save_file(self, content: bytes, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as buffer:
            buffer.write(content)
        return destination
    
    def cleanup_directory(self, directory: Path) -> None:
        if directory.exists():
            shutil.rmtree(directory)

class UploadService:
    def __init__(
        self,
        file_manager: FileManager,
        ingestion_service: DocumentIngestionService,
        temp_directory: str = "temp_pdfs"
    ):
        self.file_manager = file_manager
        self.ingestion_service = ingestion_service
        self.temp_directory = Path(temp_directory)
    
    async def process_uploads(self, files: List, urls: List[str] = None) -> Dict:
        self.temp_directory.mkdir(exist_ok=True)
        
        try:
            file_paths_with_urls = await self._save_uploaded_files(files, urls)
            
            if not file_paths_with_urls:
                return {"message": "No valid PDF files were uploaded.", "files_processed": 0}
            
            doc_count = self.ingestion_service.ingest_documents(file_paths_with_urls)
            
            self.file_manager.cleanup_directory(self.temp_directory)
            
            return {
                "message": f"Successfully ingested {doc_count} document splits from {len(file_paths_with_urls)} files.",
                "files_processed": len(file_paths_with_urls)
            }
        
        except Exception as e:
            self.file_manager.cleanup_directory(self.temp_directory)
            raise e
    
    async def _save_uploaded_files(self, files: List, urls: List[str] = None) -> Dict[str, str]:
        file_paths_with_urls = {}
        
        for idx, file in enumerate(files):
            if not file.filename.endswith('.pdf'):
                continue
            
            file_path = self.temp_directory / file.filename
            content = await file.read()
            self.file_manager.save_file(content, file_path)
            
            source_url = urls[idx] if urls and idx < len(urls) and urls[idx] else f"Uploaded: {file.filename}"
            file_paths_with_urls[str(file_path)] = source_url
        
        return file_paths_with_urls

def create_ingestion_service() -> DocumentIngestionService:
    document_loader = DocumentLoaderFactory.create_loader("pdf")
    text_splitter = TextSplitterFactory.create_splitter("tiktoken", chunk_size=500, chunk_overlap=75)
    vector_store = VectorStoreFactory.create_vector_store("chroma", "knowladge_collection", "./chroma_db")
    
    return DocumentIngestionService(document_loader, text_splitter, vector_store)

def create_upload_service() -> UploadService:
    file_manager = LocalFileManager()
    ingestion_service = create_ingestion_service()
    
    return UploadService(file_manager, ingestion_service)

def get_vector_store():
    return VectorStoreFactory.create_vector_store("chroma", "knowladge_collection", "./chroma_db")
