from abc import ABC, abstractmethod
from typing import Protocol, Dict, List
from pathlib import Path

class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: str, source_url: str) -> List:
        pass

class TextSplitter(ABC):
    @abstractmethod
    def split_documents(self, documents: List) -> List:
        pass

class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, documents: List) -> None:
        pass

class FileManager(ABC):
    @abstractmethod
    def save_file(self, content: bytes, destination: Path) -> Path:
        pass
    
    @abstractmethod
    def cleanup_directory(self, directory: Path) -> None:
        pass
