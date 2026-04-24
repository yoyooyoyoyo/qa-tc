from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".xlsx", ".xls"}


def parse_file(file_path: str | Path) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext in {".txt", ".md"}:
        return _parse_text_file(path)

    if ext == ".pdf":
        return _parse_pdf_file(path)

    if ext == ".docx":
        return _parse_docx_file(path)

    if ext in {".xlsx", ".xls"}:
        return _parse_excel_file(path)

    raise ValueError(f"Unsupported file type: {ext}")


def _parse_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _parse_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []

    for idx, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        pages.append(f"[PAGE {idx}]\n{page_text.strip()}")

    return "\n\n".join(pages).strip()


def _parse_docx_file(path: Path) -> str:
    document = Document(str(path))
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def _parse_excel_file(path: Path) -> str:
    excel_file = pd.ExcelFile(path)
    parts: list[str] = []

    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=str).fillna("")
        parts.append(f"[SHEET: {sheet_name}]")
        parts.append(df.to_csv(sep="\t", index=False))

    return "\n".join(parts).strip()