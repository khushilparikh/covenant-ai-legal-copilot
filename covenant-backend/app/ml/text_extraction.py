"""
Module 1 (Contract Ingestion): extracts raw text + page metadata from
uploaded PDF/DOCX files, then segments the text into clause-sized chunks
for the classification/risk pipeline.

PDF extraction uses PyMuPDF (fitz); if a page yields near-zero extractable
text (i.e. it's a scanned image), it's routed through pytesseract OCR so
scanned contracts are still processed (SRS: "OCR Support").
"""
import io
import re

MIN_CHARS_FOR_TEXT_PAGE = 20


def _ocr_page(page) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return "[OCR unavailable — install pytesseract and Pillow to enable scanned-document support]"
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)


def extract_pdf(file_bytes: bytes) -> dict:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        used_ocr = False
        if len(text) < MIN_CHARS_FOR_TEXT_PAGE:
            text = _ocr_page(page).strip()
            used_ocr = True
        pages.append({"page_number": i + 1, "text": text, "ocr": used_ocr})
    full_text = "\n\n".join(p["text"] for p in pages)
    return {"pages": pages, "full_text": full_text, "page_count": len(pages)}


def extract_docx(file_bytes: bytes) -> dict:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)
    # DOCX has no native page boundaries; approximate ~3000 chars/page for
    # UI display purposes only (clause extraction below doesn't depend on it).
    approx_page_size = 3000
    pages = [
        {"page_number": i // approx_page_size + 1, "text": full_text[i:i + approx_page_size], "ocr": False}
        for i in range(0, max(len(full_text), 1), approx_page_size)
    ]
    return {"pages": pages, "full_text": full_text, "page_count": max(1, len(pages))}


def extract_text(filename: str, file_bytes: bytes) -> dict:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_pdf(file_bytes)
    if lower.endswith(".docx"):
        return extract_docx(file_bytes)
    raise ValueError(f"Unsupported file type: {filename}. Only .pdf and .docx are supported.")


# --- Clause segmentation -------------------------------------------------

_CLAUSE_HEADER_RE = re.compile(
    r"^\s*(?:Section\s+)?(\d{1,2}(?:\.\d{1,2})?)\s*[\.\)]?\s+[A-Z][A-Za-z /&,\-]{2,60}\s*$",
    re.MULTILINE,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;])\s+(?=[A-Z])")


def segment_into_clauses(full_text: str, min_len: int = 60, max_len: int = 900) -> list[dict]:
    """
    Splits full contract text into clause-sized segments.

    Strategy: prefer numbered section headers (e.g. "8.3 Limitation of
    Liability") as clause boundaries, since that's how commercial contracts
    are actually structured; fall back to sentence-grouping for documents
    without numbered sections (e.g. some NDAs, letters).
    """
    header_matches = list(_CLAUSE_HEADER_RE.finditer(full_text))
    segments = []

    if len(header_matches) >= 3:
        for idx, m in enumerate(header_matches):
            start = m.start()
            end = header_matches[idx + 1].start() if idx + 1 < len(header_matches) else len(full_text)
            clause_id = m.group(1)
            body = full_text[start:end].strip()
            if len(body) >= min_len:
                segments.append({"clause_number": clause_id, "text": body[:max_len]})
    else:
        sentences = _SENTENCE_SPLIT_RE.split(full_text.replace("\n", " "))
        buffer = ""
        counter = 1
        for s in sentences:
            buffer = f"{buffer} {s}".strip()
            if len(buffer) >= min_len:
                segments.append({"clause_number": str(counter), "text": buffer[:max_len]})
                counter += 1
                buffer = ""
        if buffer.strip() and len(buffer) >= 20:
            segments.append({"clause_number": str(counter), "text": buffer[:max_len]})

    return segments
