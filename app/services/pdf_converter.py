# app/services/pdf_converter.py
import logging
import io
from typing import List
from pdf2image import convert_from_bytes

logger = logging.getLogger("uvicorn.error")

def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[bytes]:
    """
    Convert each page of a PDF file (in bytes) to PNG image bytes.
    Returns a list of image bytes (PNG format).
    Returns an empty list if conversion fails.
    """
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
        image_bytes_list = []
        for img in images:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            image_bytes_list.append(img_byte_arr.getvalue())
        return image_bytes_list
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}", exc_info=True)
        return []

def convert_first_page(pdf_bytes: bytes, dpi: int = 200) -> bytes:
    """
    Convert only the first page of a PDF file (in bytes) to PNG image bytes.
    Returns PNG image bytes, or empty bytes if conversion fails.
    """
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=1, last_page=1)
        if images:
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
    except Exception as e:
        logger.error(f"Error converting first page of PDF to image: {str(e)}", exc_info=True)
    return b""
