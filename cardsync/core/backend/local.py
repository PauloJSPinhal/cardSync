"""Backend local (filesystem) para desenvolvimento/testes."""

import os
import shutil
import hashlib
from typing import List, Dict, Any, Optional
from .base import StorageBackend
from ..hashing import md5_file


class LocalBackend(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        self._auth = True

    def authenticate(self) -> bool:
        self._auth = True
        return True

    def is_authenticated(self) -> bool:
        return self._auth

    def get_about(self) -> Dict[str, Any]:
        # quota não aplicável; devolve espaço do disco
        try:
            st = os.statvfs(self.base_dir)
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            used = total - free
            return {"used": used, "total": total, "free": free}
        except Exception:
            return {"used": 0, "total": 0, "free": 0}

    def _path(self, fid: Optional[str]) -> str:
        if fid is None or fid == "":
            return self.base_dir
        if os.path.isabs(fid):
            return fid
        return os.path.join(self.base_dir, fid)

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        parent = self._path(parent_id)
        path = os.path.join(parent, name)
        os.makedirs(path, exist_ok=True)
        return path

    def find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        parent = self._path(parent_id)
        path = os.path.join(parent, name)
        if os.path.isdir(path):
            return path
        return None

    def list_files(self, folder_id: str) -> List[Dict[str, Any]]:
        path = self._path(folder_id)
        out = []
        if not os.path.isdir(path):
            return out
        for entry in os.scandir(path):
            if entry.is_file():
                fp = entry.path
                out.append({
                    "id": fp,
                    "name": entry.name,
                    "size": entry.stat().st_size,
                    "md5": md5_file(fp),
                })
        return out

    def list_folders(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        path = self._path(parent_id)
        out = []
        if not os.path.isdir(path):
            return out
        for entry in os.scandir(path):
            if entry.is_dir():
                out.append({"id": entry.path, "name": entry.name})
        return out

    def upload_file(self, local_path: str, folder_id: str, filename: Optional[str] = None) -> str:
        folder = self._path(folder_id)
        os.makedirs(folder, exist_ok=True)
        name = filename or os.path.basename(local_path)
        dest = os.path.join(folder, name)
        shutil.copy2(local_path, dest)
        return dest

    def delete_file(self, file_id: str) -> None:
        if os.path.isfile(file_id):
            os.remove(file_id)
        elif os.path.isdir(file_id):
            shutil.rmtree(file_id)

    def create_permission(self, folder_id: str, email: str, role: str = "reader") -> str:
        # simulação: grava ficheiro de permissões na pasta 04_Docs? apenas retorna id
        return f"perm_{email}"

    def folder_url(self, folder_id: str) -> str:
        return f"file://{folder_id}"

    def ensure_structure(self, root_name: str, parent_id: Optional[str] = None) -> Dict[str, str]:
        root = self.create_folder(root_name, parent_id)
        ids = {"root": root}
        for sub in ["01_RAW", "02_JPG_Original", "03_Tratadas", "04_Docs"]:
            ids[sub] = self.create_folder(sub, root)
        return ids