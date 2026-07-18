"""
resume_parser.py — File → raw text extraction.

Two functions, one job each:
  parse_pdf(file_bytes)  → str   uses pypdf
  parse_docx(file_bytes) → str   uses python-docx

Structured extraction (skills, experience, etc.) happens downstream
in resume_agent.py via the LLM — this layer only cares about bytes → text.
"""

import io
import logging

logger = logging.getLogger(__name__)


# ── PDF ──────────────────────────────────────────────────────────────────────

def parse_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.

    How it works:
      1. Wrap bytes in an in-memory buffer (no temp files needed).
      2. Open the buffer with pypdf's PdfReader.
      3. Iterate every page, extract text, join with newlines.
      4. Strip leading/trailing whitespace and return.

    Args:
        file_bytes: Raw PDF content (e.g. from FastAPI's UploadFile.read()).

    Returns:
        Plain text string of the full document.

    Raises:
        ValueError: If the PDF has no extractable text (e.g. scanned image PDF).
        RuntimeError: If pypdf fails to read the file.
    """
    # ── Why io.BytesIO? ───────────────────────────────────────────────────────
    # pypdf (and most file-reading libs) expect a file-like object, not raw bytes.
    # io.BytesIO wraps bytes in a seekable, readable buffer — no disk I/O needed.
    try:
        from pypdf import PdfReader  # lazy import — only pay cost when called
    except ImportError as e:
        raise RuntimeError("pypdf is not installed. Run: uv add pypdf") from e

    buffer = io.BytesIO(file_bytes)

    try:
        reader = PdfReader(buffer)
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}") from e

    pages_text = []
    for page_num, page in enumerate(reader.pages):
        # extract_text() returns "" on image-only pages, not None
        text = page.extract_text() or ""
        pages_text.append(text)
        logger.debug("PDF page %d: %d chars extracted", page_num + 1, len(text))

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise ValueError(
            "No extractable text found in PDF. "
            "The file may be a scanned image — OCR is not supported yet."
        )

    logger.info("parse_pdf: extracted %d chars from %d pages", len(full_text), len(reader.pages))
    return full_text


# ── DOCX ─────────────────────────────────────────────────────────────────────

def parse_docx(file_bytes: bytes) -> str:
    """
    Extract all text from a DOCX file given its raw bytes.

    How it works:
      1. Wrap bytes in io.BytesIO (same trick as PDF).
      2. Open with python-docx's Document class.
      3. A DOCX 'paragraph' maps to a block of text (heading, bullet, body copy).
      4. Join non-empty paragraphs with newlines and return.

    Args:
        file_bytes: Raw DOCX content.

    Returns:
        Plain text string of the full document.

    Raises:
        ValueError: If the document contains no text paragraphs.
        RuntimeError: If python-docx fails to open the file.
    """
    try:
        from docx import Document  # python-docx exposes this at top level
    except ImportError as e:
        raise RuntimeError("python-docx is not installed. Run: uv add python-docx") from e

    buffer = io.BytesIO(file_bytes)

    try:
        doc = Document(buffer)
    except Exception as e:
        raise RuntimeError(f"Failed to read DOCX: {e}") from e

    # ── Why filter empty paragraphs? ──────────────────────────────────────────
    # DOCX files contain many empty paragraph objects for spacing/formatting.
    # Filtering them keeps the output clean for the LLM — less noise = better extraction.
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        raise ValueError("No text paragraphs found in DOCX file.")

    full_text = "\n".join(paragraphs)
    logger.info("parse_docx: extracted %d chars from %d paragraphs", len(full_text), len(paragraphs))
    return full_text


# ── Dispatcher ────────────────────────────────────────────────────────────────

def parse_resume(file_bytes: bytes, filename: str) -> str:
    """
    Route to the correct parser based on file extension.

    This is the function agents and API routes should call — they don't
    need to know which parser is used under the hood.

    Args:
        file_bytes: Raw file content.
        filename:   Original filename, used to detect format ("resume.pdf", "cv.docx").

    Returns:
        Extracted plain text.

    Raises:
        ValueError: On unsupported file type.
    """
    ext = filename.lower().rsplit(".", 1)[-1]  # "resume.pdf" → "pdf"

    if ext == "pdf":
        return parse_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return parse_docx(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type '.{ext}'. Upload a PDF or DOCX file."
        )
