"""Esquema do manifest.json (secção 6)."""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


SCHEMA_VERSION = "1.0"
SUBFOLDERS = ["01_RAW", "02_JPG_Original", "03_Tratadas", "04_Docs"]
FILE_TYPES = {"RAW", "JPG_ORIGINAL", "JPG_TREATED", "DOC"}


def new_manifest(project_id: str, folder_name: str, display_title: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "folder_name": folder_name,
        "display_title": display_title,
        "status": "active",  # active | frozen
        "created_at": now,
        "updated_at": now,
        "drive_ids": {
            "root_folder_id": None,
            "raw_folder_id": None,
            "jpg_folder_id": None,
            "treated_folder_id": None,
            "docs_folder_id": None,
        },
        "shared_with": [],
        "files_manifest": [],
    }


def load_manifest(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(path: str, manifest: Dict[str, Any]) -> None:
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def add_file_entry(manifest: Dict[str, Any], filename: str, ftype: str, size_bytes: int,
                   md5: str, shot_date: Optional[str] = None) -> None:
    if ftype not in FILE_TYPES:
        raise ValueError(f"Tipo de ficheiro inválido: {ftype}")
    entry = {
        "filename": filename,
        "type": ftype,
        "size_bytes": size_bytes,
        "md5": md5,
        "shot_date": shot_date,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    # evitar duplicados por nome+md5
    for existing in manifest["files_manifest"]:
        if existing["filename"] == filename and existing["md5"] == md5:
            return
    manifest["files_manifest"].append(entry)


def find_file_entry(manifest: Dict[str, Any], filename: str) -> Optional[Dict[str, Any]]:
    for e in manifest["files_manifest"]:
        if e["filename"] == filename:
            return e
    return None


def set_status(manifest: Dict[str, Any], status: str) -> None:
    if status not in ("active", "frozen"):
        raise ValueError("status deve ser 'active' ou 'frozen'")
    manifest["status"] = status


def add_shared(manifest: Dict[str, Any], email: str, permission_id: str, target_folder: str = "03_Tratadas") -> None:
    entry = {
        "email": email,
        "permission_id": permission_id,
        "granted_at": datetime.now(timezone.utc).isoformat(),
        "target_folder": target_folder,
    }
    # evitar duplicado por email
    manifest["shared_with"] = [s for s in manifest["shared_with"] if s.get("email") != email]
    manifest["shared_with"].append(entry)