from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from flask import current_app
import nh3
import markdown as md


def ensure_covers_dir() -> Path:
    covers_dir = Path(current_app.config["COVERS_DIR"])
    covers_dir.mkdir(parents=True, exist_ok=True)
    return covers_dir


def calc_md5(data: bytes) -> str:
    h = hashlib.md5()
    h.update(data)
    return h.hexdigest()


def _ext_from_mime(mime_type: str) -> Optional[str]:
    if not mime_type:
        return None
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    if mime_type.lower() in mapping:
        return mapping[mime_type.lower()]
    return mimetypes.guess_extension(mime_type)


def _ext_from_filename(filename: str) -> Optional[str]:
    if not filename:
        return None
    ext = os.path.splitext(filename)[1]
    return ext if ext else None


def save_cover_file(cover_id: int, file_bytes: bytes, mime_type: Optional[str], original_filename: Optional[str]) -> Tuple[str, Path]:
    covers_dir = ensure_covers_dir()
    ext = _ext_from_mime(mime_type or "") or _ext_from_filename(original_filename or "") or ".bin"
    filename = f"{cover_id}{ext}"
    full_path = covers_dir / filename

    with tempfile.NamedTemporaryFile("wb", delete=False, dir=str(covers_dir)) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    tmp_path.replace(full_path)
    return filename, full_path


def remove_cover_file(filename: str) -> bool:
    if not filename:
        return False
    path = ensure_covers_dir() / filename
    if path.exists():
        try:
            path.unlink()
            return True
        except OSError:
            return False
    return False


_DEFAULT_ALLOWED_TAGS = {
    "p", "div", "pre", "blockquote",
    "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "b", "em", "i", "code", "kbd", "samp",
    "hr", "br", "span",
    "a",
}

_DEFAULT_ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "span": {"class"},
    "code": {"class"},
    "pre": {"class"},
    "div": {"class"},
}

_DEFAULT_ALLOWED_PROTOCOLS = {"http", "https", "mailto"}


def markdown_to_html_safe(src_text: str) -> str:
    if not src_text:
        return ""

    extensions = current_app.config.get("MARKDOWN_EXTENSIONS", ["extra", "sane_lists", "nl2br"])
    html = md.markdown(src_text, extensions=extensions)

    allowed_tags = current_app.config.get("NH3_ALLOWED_TAGS") or _DEFAULT_ALLOWED_TAGS
    allowed_attrs = current_app.config.get("NH3_ALLOWED_ATTRS") or _DEFAULT_ALLOWED_ATTRS

    try:
        return nh3.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attrs,
            url_schemes=_DEFAULT_ALLOWED_PROTOCOLS,
        )
    except Exception:
        from markupsafe import escape
        return str(escape(src_text)).replace("\n", "<br>")



def parse_page_arg(raw: Optional[str], default: int = 1) -> int:
    try:
        val = int(raw)
        return val if val > 0 else default
    except (TypeError, ValueError):
        return default