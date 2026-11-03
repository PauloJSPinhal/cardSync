"""Leitura de metadados EXIF (secções 3.3, 5.1)."""

import os
from datetime import datetime, date
from typing import Optional, Dict, Any

try:
    import exifread
except Exception:  # pragma: no cover
    exifread = None

from PIL import Image, ExifTags


EXIF_DATETIME_ORIGINAL = "EXIF DateTimeOriginal"
EXIF_DATETIME_DIGITIZED = "EXIF DateTimeDigitized"
EXIF_MAKE = "Image Make"
EXIF_MODEL = "Image Model"
EXIF_LENS = "EXIF LensModel"
EXIF_FOCAL = "EXIF FocalLength"
EXIF_FNUMBER = "EXIF FNumber"
EXIF_EXPOSURE = "EXIF ExposureTime"
EXIF_ISO = "EXIF ISOSpeedRatings"


def _parse_exif_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # formatos comuns: "2026:11:03 10:14:22"
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def read_exif(path: str) -> Dict[str, Any]:
    """Lê metadados EXIF de um ficheiro de imagem. Retorna dict com chaves padronizadas."""
    result: Dict[str, Any] = {
        "path": path,
        "filename": os.path.basename(path),
        "datetime_original": None,
        "shot_date": None,
        "make": None,
        "model": None,
        "lens": None,
        "focal_length": None,
        "f_number": None,
        "exposure_time": None,
        "iso": None,
        "raw": {},
    }
    # Tentar exifread primeiro (melhor para RAW/CR2)
    if exifread is not None:
        try:
            with open(path, "rb") as f:
                tags = exifread.process_file(f, details=False)
            result["raw"] = {str(k): str(v) for k, v in tags.items()}
            # DateTimeOriginal
            for key in (EXIF_DATETIME_ORIGINAL, EXIF_DATETIME_DIGITIZED):
                if key in tags:
                    dt = _parse_exif_datetime(tags[key])
                    if dt is not None:
                        result["datetime_original"] = dt
                        break
            result["make"] = str(tags.get(EXIF_MAKE, "")).strip() or None
            result["model"] = str(tags.get(EXIF_MODEL, "")).strip() or None
            result["lens"] = str(tags.get(EXIF_LENS, "")).strip() or None
            if EXIF_FOCAL in tags:
                result["focal_length"] = str(tags[EXIF_FOCAL]).strip()
            if EXIF_FNUMBER in tags:
                result["f_number"] = str(tags[EXIF_FNUMBER]).strip()
            if EXIF_EXPOSURE in tags:
                result["exposure_time"] = str(tags[EXIF_EXPOSURE]).strip()
            if EXIF_ISO in tags:
                result["iso"] = str(tags[EXIF_ISO]).strip()
        except Exception:
            pass

    # Fallback PIL para JPGs
    if result["datetime_original"] is None:
        try:
            with Image.open(path) as im:
                exif = im.getexif()
                if exif:
                    tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
                    # DateTimeOriginal pode estar em sub-IFD
                    dto = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
                    dt = _parse_exif_datetime(dto)
                    if dt is not None:
                        result["datetime_original"] = dt
                    if result["make"] is None:
                        result["make"] = tag_map.get("Make")
                    if result["model"] is None:
                        result["model"] = tag_map.get("Model")
        except Exception:
            pass

    if result["datetime_original"] is not None:
        result["shot_date"] = result["datetime_original"].date()
    return result


def shot_date(path: str) -> Optional[date]:
    info = read_exif(path)
    return info.get("shot_date")