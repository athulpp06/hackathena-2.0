"""
ocr.py - Utility wrapper exposing extract_text_from_image and get_reader.
Provides EasyOCR interface mocked in tests with seamless fallback to Tesseract/WinOCR.
"""

import sys

# Optional easyocr reader instance
_reader = None


def get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(['en'], gpu=False)
        except Exception:
            _reader = None
    return _reader


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text from an image.
    If EasyOCR reader is active (or mocked in unit tests), uses it.
    Otherwise uses high-performance native Windows/Tesseract OCR engine.
    """
    try:
        reader = get_reader()
        if reader is not None:
            results = reader.readtext(image_bytes, detail=0)
            extracted_text = " ".join(results)
            if not extracted_text.strip():
                return "No text could be extracted from the image."
            return extracted_text
    except Exception as e:
        raise ValueError(f"Failed to extract text using EasyOCR: {e!s}") from e

    # Fallback to backend.app.ocr (Tesseract / WinOCR)
    from backend.app.ocr import extract_text_from_image as native_extract
    return native_extract(image_bytes)
