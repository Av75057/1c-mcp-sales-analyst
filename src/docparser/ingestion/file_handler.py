from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any

from PIL import Image

from src.logger import logger

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".tiff", ".tif", ".txt", ".csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_PAGES = 10


def validate_file(filename: str, data: bytes) -> dict[str, Any]:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"valid": False, "error": f"Недопустимый формат: {ext}. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"}
    if len(data) > MAX_FILE_SIZE:
        return {"valid": False, "error": f"Файл слишком большой: {len(data)} байт (максимум {MAX_FILE_SIZE})"}
    file_hash = hashlib.sha256(data).hexdigest()
    return {"valid": True, "ext": ext, "file_hash": file_hash, "size": len(data)}


def pdf_to_images(data: bytes, max_pages: int = MAX_PAGES) -> list[bytes]:
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF не установлен. Установи: pip install pymupdf")
        return []

    images: list[bytes] = []
    doc = fitz.open(stream=data, filetype="pdf")
    for page_num in range(min(len(doc), max_pages)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
        img_data = pix.tobytes("jpeg")
        images.append(img_data)
    doc.close()
    logger.info("PDF: {} страниц → {} изображений", len(doc), len(images))
    return images


def preprocess_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    max_dim = 2048
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def load_image(filename: str, data: bytes) -> list[bytes]:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return pdf_to_images(data)
    img = preprocess_image(data)
    return [img]
