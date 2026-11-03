"""Backend Google Drive via API v3."""

import os
import json
from typing import List, Dict, Any, Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
    GOOGLE_AVAILABLE = True
except Exception:
    GOOGLE_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"


class GoogleDriveBackend:
    def __init__(self, client_secrets_path: Optional[str] = None, token_path: Optional[str] = None):
        self.client_secrets_path = client_secrets_path
        self.token_path = token_path or os.path.expanduser("~/.config/cardsync/token.json")
        self.creds = None
        self.service = None

    def authenticate(self) -> bool:
        if not GOOGLE_AVAILABLE:
            return False
        # carregar token existente
        if os.path.exists(self.token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception:
                self.creds = None
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
            except Exception:
                self.creds = None
        if not self.creds or not self.creds.valid:
            if not self.client_secrets_path or not os.path.exists(self.client_secrets_path):
                return False
            try:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            except Exception:
                return False
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, "w") as f:
                f.write(self.creds.to_json())
        try:
            self.service = build("drive", "v3", credentials=self.creds)
            return True
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        return self.service is not None

    def get_about(self) -> Dict[str, Any]:
        if not self.service:
            return {}
        try:
            res = self.service.about().get(fields="storageQuota").execute()
            q = res.get("storageQuota", {})
            return {
                "used": int(q.get("usage", 0)),
                "total": int(q.get("limit", 0)),
                "free": int(q.get("limit", 0)) - int(q.get("usage", 0)),
            }
        except Exception:
            return {}

    def _find(self, name: str, parent_id: Optional[str], mime: Optional[str] = None) -> Optional[str]:
        if not self.service:
            return None
        q = f"name = '{name.replace(chr(39), chr(92)+chr(39))}' and trashed = false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        if mime:
            q += f" and mimeType = '{mime}'"
        try:
            res = self.service.files().list(q=q, spaces="drive", fields="files(id,name)").execute()
            files = res.get("files", [])
            if files:
                return files[0]["id"]
        except Exception:
            pass
        return None

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        if not self.service:
            raise RuntimeError("Não autenticado")
        meta = {"name": name, "mimeType": FOLDER_MIME}
        if parent_id:
            meta["parents"] = [parent_id]
        res = self.service.files().create(body=meta, fields="id").execute()
        return res["id"]

    def find_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        return self._find(name, parent_id, mime=FOLDER_MIME)

    def list_files(self, folder_id: str) -> List[Dict[str, Any]]:
        if not self.service:
            return []
        out = []
        page_token = None
        while True:
            res = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false and mimeType != '{FOLDER_MIME}'",
                spaces="drive",
                fields="nextPageToken, files(id,name,size,md5Checksum)",
                pageToken=page_token,
            ).execute()
            for f in res.get("files", []):
                out.append({
                    "id": f["id"],
                    "name": f["name"],
                    "size": int(f.get("size", 0)),
                    "md5": f.get("md5Checksum"),
                })
            page_token = res.get("nextPageToken")
            if not page_token:
                break
        return out

    def list_folders(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.service:
            return []
        q = f"mimeType = '{FOLDER_MIME}' and trashed = false"
        if parent_id:
            q = f"'{parent_id}' in parents and mimeType = '{FOLDER_MIME}' and trashed = false"
        out = []
        page_token = None
        while True:
            res = self.service.files().list(q=q, spaces="drive", fields="nextPageToken, files(id,name)", pageToken=page_token).execute()
            for f in res.get("files", []):
                out.append({"id": f["id"], "name": f["name"]})
            page_token = res.get("nextPageToken")
            if not page_token:
                break
        return out

    def upload_file(self, local_path: str, folder_id: str, filename: Optional[str] = None) -> str:
        if not self.service:
            raise RuntimeError("Não autenticado")
        name = filename or os.path.basename(local_path)
        media = MediaFileUpload(local_path, resumable=True)
        meta = {"name": name, "parents": [folder_id]}
        res = self.service.files().create(body=meta, media_body=media, fields="id").execute()
        return res["id"]

    def delete_file(self, file_id: str) -> None:
        if not self.service:
            return
        try:
            self.service.files().delete(fileId=file_id).execute()
        except Exception:
            pass

    def create_permission(self, folder_id: str, email: str, role: str = "reader") -> str:
        if not self.service:
            raise RuntimeError("Não autenticado")
        body = {"type": "user", "role": role, "emailAddress": email}
        res = self.service.permissions().create(fileId=folder_id, body=body, fields="id").execute()
        return res["id"]

    def folder_url(self, folder_id: str) -> str:
        return f"https://drive.google.com/drive/folders/{folder_id}"

    def ensure_structure(self, root_name: str, parent_id: Optional[str] = None) -> Dict[str, str]:
        # procura ou cria pasta raiz
        root = self.find_folder(root_name, parent_id)
        if root is None:
            root = self.create_folder(root_name, parent_id)
        ids = {"root": root}
        for sub in ["01_RAW", "02_JPG_Original", "03_Tratadas", "04_Docs"]:
            sid = self.find_folder(sub, root)
            if sid is None:
                sid = self.create_folder(sub, root)
            ids[sub] = sid
        return ids