from dotenv import load_dotenv
from services import create_ingestion_service

load_dotenv()

_ingestion_service = None

def get_ingestion_service():
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = create_ingestion_service()
    return _ingestion_service

def ingest_pdfs(file_paths_with_urls):
    service = get_ingestion_service()
    return service.ingest_documents(file_paths_with_urls)
