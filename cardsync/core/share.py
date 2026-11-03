"""Partilha e comunicação (secção 4)."""

import os
import io
import base64
from typing import List, Dict, Any, Optional
from .backend.base import StorageBackend

try:
    import qrcode
    QR_AVAILABLE = True
except Exception:
    QR_AVAILABLE = False


def share_folder_with_emails(backend: StorageBackend, treated_folder_id: str,
                             emails: List[str]) -> List[Dict[str, Any]]:
    results = []
    for email in emails:
        email = email.strip()
        if not email:
            continue
        try:
            perm_id = backend.create_permission(treated_folder_id, email, role="reader")
            results.append({"email": email, "permission_id": perm_id, "ok": True})
        except Exception as e:
            results.append({"email": email, "permission_id": None, "ok": False, "error": str(e)})
    return results


def folder_link(backend: StorageBackend, treated_folder_id: str) -> str:
    return backend.folder_url(treated_folder_id)


def generate_qr_png(url: str, out_path: Optional[str] = None, size: int = 8) -> Optional[str]:
    if not QR_AVAILABLE:
        return None
    img = qrcode.make(url)
    if out_path:
        img.save(out_path)
        return out_path
    # guardar em temp
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(path)
    return path


def generate_qr_bytes(url: str) -> Optional[bytes]:
    if not QR_AVAILABLE:
        return None
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def whatsapp_message(event: str, location: str, url: str) -> str:
    return (f"Olá! As fotos tratadas de {event}, {location} já estão disponíveis:\n"
            f"{url}\n")


def whatsapp_intent_url(message: str) -> str:
    import urllib.parse
    return "https://wa.me/?text=" + urllib.parse.quote(message)


def email_html(event: str, location: str, date_str: str, total_photos: int,
               treated_folder_url: str, thumbnails: List[str] = None) -> str:
    thumbnails = thumbnails or []
    thumbs_html = ""
    for t in thumbnails:
        thumbs_html += f'<img src="{t}" style="width:120px;height:80px;object-fit:cover;margin:4px;border-radius:4px;" />\n'
    return f"""<p>Olá,</p>
<p>As fotografias tratadas de <strong>{event}</strong> em <strong>{location}</strong> já se encontram disponíveis.</p>
<div style="display: flex; gap: 8px; flex-wrap: wrap;">
{thumbs_html}
</div>
<p style="margin-top: 16px;">
  <a href="{treated_folder_url}"
     style="background-color: #1a73e8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
     Ver Álbum Completo ({total_photos} Fotografias)
  </a>
</p>"""


def email_subject(event: str, location: str, date_str: str) -> str:
    return f"Fotos disponíveis: {event}, {location} ({date_str})"