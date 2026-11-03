"""Triagem por extensão e separação por data de captura (secções 3.2, 3.3)."""

import os
from typing import List, Dict, Any, Callable
from .naming import folder_name, format_date_yyyymmdd
from .exif import read_exif, shot_date as exif_shot_date

RAW_EXTS = {"cr2", "cr3", "dng"}
JPG_EXTS = {"jpg", "jpeg"}


def ext_of(path: str) -> str:
    return os.path.splitext(path)[1].lstrip(".").lower()


def classify(path: str, treated: bool = False) -> str:
    """Retorna subpasta destino para um ficheiro."""
    e = ext_of(path)
    if e in RAW_EXTS:
        return "01_RAW"
    if e in JPG_EXTS:
        return "03_Tratadas" if treated else "02_JPG_Original"
    return None


def group_files(paths: List[str], event: str, location: str,
               target_date=None, treated: bool = False,
               shot_date_resolver: Callable[[str], Any] = None) -> Dict[str, Dict[str, List[str]]]:
    """
    Agrupa ficheiros por pasta raiz (por data de disparo) e subpasta.
    Retorna {root_folder_name: {subfolder: [paths]}}.
    """
    if shot_date_resolver is None:
        shot_date_resolver = exif_shot_date

    result: Dict[str, Dict[str, List[str]]] = {}
    for p in paths:
        sub = classify(p, treated=treated)
        if sub is None:
            continue
        # data de disparo
        sd = shot_date_resolver(p)
        if sd is None:
            # usar target_date ou data do sistema
            if target_date is not None:
                sd = target_date
            else:
                from datetime import date
                sd = date.today()
        root = folder_name(sd, event, location)
        result.setdefault(root, {}).setdefault(sub, []).append(p)
    return result


def list_supported(paths: List[str]) -> List[str]:
    out = []
    for p in paths:
        if ext_of(p) in RAW_EXTS or ext_of(p) in JPG_EXTS:
            out.append(p)
    return out