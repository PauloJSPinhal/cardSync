"""Orquestração de coleções: criação, upload deduplicado, congelamento (secção 3)."""

import os
from typing import Dict, Any, List, Optional, Callable
from .naming import folder_name, project_id, display_title, format_date_yyyymmdd
from .hashing import md5_file
from .manifest import new_manifest, save_manifest, add_file_entry, set_status
from .exif import read_exif
from .importer import classify
from .backend.base import StorageBackend


def create_collection(backend: StorageBackend, date_value, event: str, location: str,
                     parent_id: Optional[str] = None) -> Dict[str, Any]:
    root_name = folder_name(date_value, event, location)
    ids = backend.ensure_structure(root_name, parent_id=parent_id)
    pid = project_id(date_value, event)
    disp = display_title(date_value, event, location)
    manifest = new_manifest(pid, root_name, disp)
    # preencher drive_ids
    manifest["drive_ids"] = {
        "root_folder_id": ids["root"],
        "raw_folder_id": ids["01_RAW"],
        "jpg_folder_id": ids["02_JPG_Original"],
        "treated_folder_id": ids["03_Tratadas"],
        "docs_folder_id": ids["04_Docs"],
    }
    return {"root_name": root_name, "ids": ids, "manifest": manifest}


def _subfolder_id(manifest: Dict[str, Any], sub: str) -> str:
    mapping = {
        "01_RAW": "raw_folder_id",
        "02_JPG_Original": "jpg_folder_id",
        "03_Tratadas": "treated_folder_id",
        "04_Docs": "docs_folder_id",
    }
    return manifest["drive_ids"][mapping[sub]]


def _ftype_for_sub(sub: str) -> str:
    return {
        "01_RAW": "RAW",
        "02_JPG_Original": "JPG_ORIGINAL",
        "03_Tratadas": "JPG_TREATED",
    }.get(sub, "DOC")


def upload_files(backend: StorageBackend, manifest: Dict[str, Any],
                 grouped: Dict[str, Dict[str, List[str]]],
                 progress_cb: Optional[Callable[[str, int, int], None]] = None,
                 dedup: bool = True) -> Dict[str, Any]:
    """Faz upload dos ficheiros agrupados. grouped: {root_folder: {sub: [paths]}}.
    Se houver várias raízes (datas diferentes), cria estruturas separadas? 
    Esta função assume uma única coleção (manifest). Para múltiplas datas, chamar por raiz.
    """
    # inventário remoto por subpasta (para dedup)
    remote_by_sub = {}
    for sub in ["01_RAW", "02_JPG_Original", "03_Tratadas"]:
        fid = _subfolder_id(manifest, sub)
        try:
            remote_by_sub[sub] = backend.list_files(fid)
        except Exception:
            remote_by_sub[sub] = []

    total = sum(len(paths) for subs in grouped.values() for paths in subs.values())
    done = 0
    skipped = 0
    uploaded = 0
    for root_name, subs in grouped.items():
        for sub, paths in subs.items():
            fid = _subfolder_id(manifest, sub)
            remote_md5s = {f.get("md5") for f in remote_by_sub.get(sub, []) if f.get("md5")}
            remote_names = {f.get("name") for f in remote_by_sub.get(sub, [])}
            for local_path in paths:
                fname = os.path.basename(local_path)
                local_md5 = md5_file(local_path)
                # dedup por MD5
                if dedup and local_md5 in remote_md5s:
                    skipped += 1
                    done += 1
                    if progress_cb:
                        progress_cb(fname, done, total)
                    continue
                # dedup por nome (fallback)
                if dedup and fname in remote_names:
                    # verificar md5 remoto
                    remote_entry = next((f for f in remote_by_sub[sub] if f.get("name") == fname), None)
                    if remote_entry and remote_entry.get("md5") == local_md5:
                        skipped += 1
                        done += 1
                        if progress_cb:
                            progress_cb(fname, done, total)
                        continue
                # upload
                backend.upload_file(local_path, fid, filename=fname)
                uploaded += 1
                exif = read_exif(local_path)
                shot = exif.get("datetime_original")
                shot_str = shot.isoformat() if shot else None
                add_file_entry(manifest, fname, _ftype_for_sub(sub), os.path.getsize(local_path), local_md5, shot_str)
                done += 1
                if progress_cb:
                    progress_cb(fname, done, total)
    return {"total": total, "uploaded": uploaded, "skipped": skipped}


def save_manifest_remote(backend: StorageBackend, manifest: Dict[str, Any]) -> None:
    """Guarda manifest.json na pasta 04_Docs (local ou remoto)."""
    import tempfile, json
    docs_id = manifest["drive_ids"]["docs_folder_id"]
    # escrever para ficheiro temporário
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        backend.upload_file(tmp, docs_id, filename="manifest.json")
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def freeze_collection(backend: StorageBackend, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Valida integridade MD5 entre local? Apenas marca status frozen e guarda manifest."""
    set_status(manifest, "frozen")
    save_manifest_remote(backend, manifest)
    return manifest