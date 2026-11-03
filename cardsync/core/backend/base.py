"""Interface abstrata de backend de armazenamento (secção 3, 4)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StorageBackend(ABC):
    @abstractmethod
    def authenticate(self) -> bool:
        ...

    @abstractmethod
    def is_authenticated(self) -> bool:
        ...

    @abstractmethod
    def get_about(self) -> Dict[str, Any]:
        """Retorna info de quota: {'used': bytes, 'total': bytes} (ou None)."""
        ...

    @abstractmethod
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        ...

    @abstractmethod
    def find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        ...

    @abstractmethod
    def list_files(self, folder_id: str) -> List[Dict[str, Any]]:
        """Lista ficheiros (não pastas) com name, size, md5/id."""
        ...

    @abstractmethod
    def list_folders(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def upload_file(self, local_path: str, folder_id: str, filename: Optional[str] = None) -> str:
        ...

    @abstractmethod
    def delete_file(self, file_id: str) -> None:
        ...

    @abstractmethod
    def create_permission(self, folder_id: str, email: str, role: str = "reader") -> str:
        ...

    @abstractmethod
    def folder_url(self, folder_id: str) -> str:
        ...

    @abstractmethod
    def ensure_structure(self, root_name: str) -> Dict[str, str]:
        """Cria/obtém pasta raiz com subpastas; retorna dict de ids por nome."""
        ...