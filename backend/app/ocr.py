"""
OCR Module for LeakedIn.
Extracts text from uploaded images and screenshots using:
1. Tesseract OCR (if installed)
2. Windows Native OCR / winocr (built-in Windows 10/11 engine) as zero-config fallback.

Supports JPEG, PNG, WebP, BMP, TIFF formats.
"""

import os
import io
import logging
from typing import Tuple, Optional

from PIL import Image, ImageEnhance
import pytesseract

logger = logging.getLogger(__name__)

# Check winocr availability
try:
    import winocr
    _HAS_WINOCR = True
except ImportError:
    _HAS_WINOCR = False

# Tesseract binary path — auto-detected on Windows
_TESSERACT_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\HP\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
]


def _configure_tesseract() -> bool:
    """Auto-detect and configure Tesseract path on Windows."""
    try:
        import shutil
        if shutil.which("tesseract"):
            return True
    except Exception:
        pass

    for path in _TESSERACT_WINDOWS_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Tesseract found at: {path}")
            return True

    return False


def get_ocr_engine() -> Optional[str]:
    """Returns the name of the active OCR engine, or None if unavailable."""
    if _configure_tesseract():
        try:
            pytesseract.get_tesseract_version()
            return "Tesseract OCR"
        except Exception:
            pass

    if _HAS_WINOCR:
        return "Windows Native OCR"

    return None


def is_ocr_available() -> bool:
    """Returns True if any OCR engine (Tesseract or Windows Native) is ready."""
    return get_ocr_engine() is not None


def _preprocess_image(image: Image.Image) -> Image.Image:
    """
    Apply preprocessing to improve OCR accuracy on job posting screenshots.
    - Convert to RGB (handles transparency from PNG)
    - Upscale small images to ensure legible text
    - Enhance contrast and sharpness
    """
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode in ('RGBA', 'LA'):
            background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # Upscale if image is smaller than standard screenshot
    width, height = image.size
    if width < 1200:
        scale = 1200 / width
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.LANCZOS)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.4)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.8)

    return image


async def extract_text_from_image_bytes(image_bytes: bytes, filename: str = "") -> Tuple[str, float]:
    """
    Extracts text from raw image bytes using the best available OCR engine.

    Returns
    -------
    Tuple of (extracted_text: str, confidence: float 0.0-1.0)
    """
    engine = get_ocr_engine()
    if not engine:
        raise RuntimeError(
            "No OCR engine is available. "
            "Please install Tesseract OCR or run on Windows 10/11."
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Could not open image '{filename}': {e}")

    processed = _preprocess_image(image)

    # 1. Try Tesseract first if configured
    if engine == "Tesseract OCR":
        try:
            gray = processed.convert('L')
            custom_config = r'--oem 3 --psm 6'
            data = pytesseract.image_to_data(
                gray, config=custom_config, output_type=pytesseract.Output.DICT
            )
            confidences = [int(c) for c in data['conf'] if int(c) > 0]
            mean_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.8
            extracted = pytesseract.image_to_string(gray, config=custom_config).strip()
            if extracted:
                logger.info(f"Tesseract extracted {len(extracted)} chars with {mean_confidence:.0%} confidence")
                return extracted, round(mean_confidence, 3)
        except Exception as e:
            logger.warning(f"Tesseract failed, falling back to secondary OCR: {e}")

    # 2. Windows Native OCR (winocr)
    if _HAS_WINOCR:
        try:
            result = await winocr.recognize_pil(processed, 'en-US')
            # Extract line-by-line for clean paragraphs
            if hasattr(result, "lines") and result.lines:
                lines = [line.text.strip() for line in result.lines if line.text.strip()]
                extracted = "\n".join(lines)
            else:
                extracted = (result.text or "").strip()

            confidence = 0.88 if len(extracted) > 50 else 0.70
            logger.info(f"Windows Native OCR extracted {len(extracted)} chars from '{filename}'")
            return extracted, confidence
        except Exception as e:
            raise RuntimeError(f"Windows Native OCR extraction failed: {e}")

    raise RuntimeError("OCR text extraction failed with all available engines.")


def extract_text_from_image(image_bytes: bytes) -> str:
    """Synchronous helper for scripts and background workers to extract text from image bytes."""
    import asyncio
    try:
        return asyncio.run(extract_text_from_image_bytes(image_bytes))[0]
    except RuntimeError:
        # Handle already running event loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(extract_text_from_image_bytes(image_bytes))[0]).result()
