from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.core.extractor import extract_requirements_from_text
from app.core.parser import parse_file
from app.schemas.requirement import ExtractRequirementsResponse

app = FastAPI(title="QA TC Agent")

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "inputs"
INPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def read_root():
    return {"message": "QA TC Agent is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    extension = Path(file.filename).suffix.lower()
    saved_name = f"{uuid4().hex}{extension}"
    saved_path = INPUT_DIR / saved_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"File save failed: {exc}") from exc
    finally:
        file.file.close()

    return {
        "message": "File uploaded successfully",
        "original_filename": file.filename,
        "saved_filename": saved_name,
        "saved_path": str(saved_path),
    }


@app.post("/parse")
async def upload_and_parse(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    extension = Path(file.filename).suffix.lower()
    saved_name = f"{uuid4().hex}{extension}"
    saved_path = INPUT_DIR / saved_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed_text = parse_file(saved_path)

        return {
            "message": "File uploaded and parsed successfully",
            "original_filename": file.filename,
            "saved_filename": saved_name,
            "text_preview": parsed_text[:3000],
            "text_length": len(parsed_text),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Parse failed: {exc}") from exc
    finally:
        file.file.close()


@app.get("/parse-local")
def parse_local_file(filename: str):
    target_path = INPUT_DIR / filename

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        parsed_text = parse_file(target_path)
        return {
            "filename": filename,
            "text_preview": parsed_text[:3000],
            "text_length": len(parsed_text),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Parse failed: {exc}") from exc


@app.post(
    "/extract-requirements",
    response_model=ExtractRequirementsResponse,
)
async def upload_and_extract_requirements(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    extension = Path(file.filename).suffix.lower()
    saved_name = f"{uuid4().hex}{extension}"
    saved_path = INPUT_DIR / saved_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed_text = parse_file(saved_path)
        requirements = extract_requirements_from_text(parsed_text)

        return ExtractRequirementsResponse(
            message="File uploaded, parsed, and requirements extracted successfully",
            filename=file.filename,
            text_length=len(parsed_text),
            requirement_count=len(requirements),
            requirements=requirements,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Requirement extraction failed: {exc}",
        ) from exc
    finally:
        file.file.close()


@app.get(
    "/extract-requirements-local",
    response_model=ExtractRequirementsResponse,
)
def extract_requirements_local(filename: str):
    target_path = INPUT_DIR / filename

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        parsed_text = parse_file(target_path)
        requirements = extract_requirements_from_text(parsed_text)

        return ExtractRequirementsResponse(
            message="Local file parsed and requirements extracted successfully",
            filename=filename,
            text_length=len(parsed_text),
            requirement_count=len(requirements),
            requirements=requirements,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Requirement extraction failed: {exc}",
        ) from exc