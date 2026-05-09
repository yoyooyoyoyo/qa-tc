from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile

from app.core.exporter import testcases_to_tsv, testcases_to_xlsx
from app.core.extractor import extract_requirements_from_text
from app.core.figma_parser import extract_figma_context, figma_context_to_prompt_text
from app.core.gap_reporter import analysis_to_gap_report_markdown
from app.core.parser import parse_file
from app.core.policy_loader import load_policy_context
from app.core.requirement_analyzer import analyze_requirements
from app.schemas.analysis import ExportGapReportRequest
from app.core.testcase_generator import generate_testcases_from_requirements
from app.schemas.figma import ExtractFigmaContextResponse
from app.schemas.figma import FigmaContext
from app.schemas.requirement import ExtractRequirementsResponse
from app.schemas.testcase import (
    ExportTestCasesRequest,
    GenerateTestCasesFromDocumentResponse,
    GenerateTestCasesResponse,
    TestCaseGenerationRequest,
)

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


@app.post(
    "/extract-figma-context",
    response_model=ExtractFigmaContextResponse,
)
def extract_figma_context_api(
    figma_url: str = Form(..., description="Figma file/frame URL"),
    include_images: bool = Form(default=False),
    max_screens: int = Form(default=30),
):
    try:
        context = extract_figma_context(
            figma_url,
            include_images=include_images,
            max_screens=max_screens,
        )
        return ExtractFigmaContextResponse(
            message="Figma context extracted successfully",
            context=context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Figma context extraction failed: {exc}",
        ) from exc


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
async def upload_and_extract_requirements(
    file: UploadFile | None = File(
        default=None,
        description="분석할 기획서 파일(txt, md, pdf, docx, xlsx, xls)",
    ),
    text: str | None = Form(
        default=None,
        description="파일 대신 바로 분석할 기획서 텍스트",
    ),
):
    try:
        filename, parsed_text = _load_extract_source(file=file, text=text)
        requirements = extract_requirements_from_text(parsed_text)

        return ExtractRequirementsResponse(
            message="Requirements extracted successfully",
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
    finally:
        if file is not None:
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


@app.post(
    "/generate-testcases",
    response_model=GenerateTestCasesResponse,
)
def generate_testcases(request: TestCaseGenerationRequest):
    try:
        analysis = analyze_requirements(request.requirements)
        testcases = generate_testcases_from_requirements(
            requirements=request.requirements,
            perspectives=request.perspectives,
            analysis=analysis,
        )

        return GenerateTestCasesResponse(
            message="Testcases generated successfully",
            requirement_count=len(request.requirements),
            testcase_count=len(testcases),
            analysis=analysis,
            testcases=testcases,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Testcase generation failed: {exc}",
        ) from exc


@app.post(
    "/generate-testcases-from-document",
    response_model=GenerateTestCasesFromDocumentResponse,
)
async def generate_testcases_from_document(
    file: UploadFile | None = File(
        default=None,
        description="분석할 기획서 파일(txt, md, pdf, docx, xlsx, xls)",
    ),
    text: str | None = Form(
        default=None,
        description="파일 대신 바로 분석할 기획서 텍스트",
    ),
    perspectives: str = Form(
        default="PM,DEV,QA",
        description="쉼표로 구분한 테스트케이스 생성 관점",
    ),
    figma_url: str | None = Form(
        default=None,
        description="선택: Figma file/frame URL",
    ),
    figma_context: str | None = Form(
        default=None,
        description="선택: Figma MCP 등에서 추출한 화면/텍스트 컨텍스트",
    ),
    include_figma_images: bool = Form(
        default=False,
        description="선택: Figma frame 이미지 URL도 함께 추출",
    ),
):
    try:
        filename, parsed_text = _load_extract_source(file=file, text=text)
        selected_perspectives = _parse_perspectives(perspectives)
        requirements = extract_requirements_from_text(parsed_text)
        figma_api_context = _load_figma_context(
            figma_url=figma_url,
            include_images=include_figma_images,
        )
        figma_prompt_context = _build_figma_prompt_context(
            figma_context=figma_api_context,
            figma_context_text=figma_context,
        )
        policy_context = load_policy_context(parsed_text, figma_prompt_context).text
        analysis = analyze_requirements(
            requirements,
            policy_context=policy_context,
        )
        testcases = generate_testcases_from_requirements(
            requirements=requirements,
            perspectives=selected_perspectives,
            analysis=analysis,
            figma_context=figma_prompt_context,
            policy_context=policy_context,
        )

        return GenerateTestCasesFromDocumentResponse(
            message="Requirements extracted and testcases generated successfully",
            filename=filename,
            text_length=len(parsed_text),
            requirement_count=len(requirements),
            testcase_count=len(testcases),
            analysis=analysis,
            figma_context=figma_api_context,
            requirements=requirements,
            testcases=testcases,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document testcase generation failed: {exc}",
        ) from exc
    finally:
        if file is not None:
            file.file.close()


@app.post("/export-testcases-tsv")
def export_testcases_tsv(request: ExportTestCasesRequest):
    try:
        tsv_content = testcases_to_tsv(request.testcases)
        filename = _safe_export_filename(request.filename, "tsv")

        return Response(
            content=tsv_content,
            media_type="text/tab-separated-values; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"TSV export failed: {exc}",
        ) from exc


@app.post("/export-testcases-xlsx")
def export_testcases_xlsx(request: ExportTestCasesRequest):
    try:
        xlsx_content = testcases_to_xlsx(request.testcases)
        filename = _safe_export_filename(request.filename, "xlsx")

        return Response(
            content=xlsx_content,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"XLSX export failed: {exc}",
        ) from exc


@app.post("/export-gap-report-md")
def export_gap_report_md(request: ExportGapReportRequest):
    try:
        content = analysis_to_gap_report_markdown(
            request.analysis,
            title=request.title,
        )
        filename = _safe_export_filename(request.title, "md")

        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Gap report export failed: {exc}",
        ) from exc


@app.post("/export-testcases-from-document-tsv")
async def export_testcases_from_document_tsv(
    file: UploadFile | None = File(
        default=None,
        description="분석할 기획서 파일(txt, md, pdf, docx, xlsx, xls)",
    ),
    text: str | None = Form(
        default=None,
        description="파일 대신 바로 분석할 기획서 텍스트",
    ),
    perspectives: str = Form(
        default="PM,DEV,QA",
        description="쉼표로 구분한 테스트케이스 생성 관점",
    ),
    filename: str = Form(
        default="testcases",
        description="확장자를 제외한 다운로드 파일명",
    ),
    figma_url: str | None = Form(
        default=None,
        description="선택: Figma file/frame URL",
    ),
    figma_context: str | None = Form(
        default=None,
        description="선택: Figma MCP 등에서 추출한 화면/텍스트 컨텍스트",
    ),
):
    try:
        testcases = _generate_testcases_from_source(
            file=file,
            text=text,
            perspectives=perspectives,
            figma_url=figma_url,
            figma_context=figma_context,
        )
        tsv_content = testcases_to_tsv(testcases)
        export_filename = _safe_export_filename(filename, "tsv")

        return Response(
            content=tsv_content,
            media_type="text/tab-separated-values; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{export_filename}"',
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document TSV export failed: {exc}",
        ) from exc
    finally:
        if file is not None:
            file.file.close()


@app.post("/export-testcases-from-document-xlsx")
async def export_testcases_from_document_xlsx(
    file: UploadFile | None = File(
        default=None,
        description="분석할 기획서 파일(txt, md, pdf, docx, xlsx, xls)",
    ),
    text: str | None = Form(
        default=None,
        description="파일 대신 바로 분석할 기획서 텍스트",
    ),
    perspectives: str = Form(
        default="PM,DEV,QA",
        description="쉼표로 구분한 테스트케이스 생성 관점",
    ),
    filename: str = Form(
        default="testcases",
        description="확장자를 제외한 다운로드 파일명",
    ),
    figma_url: str | None = Form(
        default=None,
        description="선택: Figma file/frame URL",
    ),
    figma_context: str | None = Form(
        default=None,
        description="선택: Figma MCP 등에서 추출한 화면/텍스트 컨텍스트",
    ),
):
    try:
        testcases = _generate_testcases_from_source(
            file=file,
            text=text,
            perspectives=perspectives,
            figma_url=figma_url,
            figma_context=figma_context,
        )
        xlsx_content = testcases_to_xlsx(testcases)
        export_filename = _safe_export_filename(filename, "xlsx")

        return Response(
            content=xlsx_content,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{export_filename}"',
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document XLSX export failed: {exc}",
        ) from exc
    finally:
        if file is not None:
            file.file.close()


@app.post("/export-gap-report-from-document-md")
async def export_gap_report_from_document_md(
    file: UploadFile | None = File(
        default=None,
        description="분석할 기획서 파일(txt, md, pdf, docx, xlsx, xls)",
    ),
    text: str | None = Form(
        default=None,
        description="파일 대신 바로 분석할 기획서 텍스트",
    ),
    filename: str = Form(
        default="gap_report",
        description="확장자를 제외한 다운로드 파일명",
    ),
    figma_url: str | None = Form(
        default=None,
        description="선택: Figma file/frame URL",
    ),
    figma_context: str | None = Form(
        default=None,
        description="선택: Figma MCP 등에서 추출한 화면/텍스트 컨텍스트",
    ),
):
    try:
        _, parsed_text = _load_extract_source(file=file, text=text)
        requirements = extract_requirements_from_text(parsed_text)
        figma_prompt_context = _load_figma_prompt_context(
            figma_url=figma_url,
            figma_context_text=figma_context,
        )
        policy_context = load_policy_context(parsed_text, figma_prompt_context).text
        analysis = analyze_requirements(requirements, policy_context=policy_context)
        content = analysis_to_gap_report_markdown(analysis)
        export_filename = _safe_export_filename(filename, "md")

        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{export_filename}"',
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Gap report document export failed: {exc}",
        ) from exc
    finally:
        if file is not None:
            file.file.close()


def _load_extract_source(
    *,
    file: UploadFile | None,
    text: str | None,
) -> tuple[str, str]:
    if text and text.strip():
        return "inline-text", text.strip()

    if file is None:
        raise ValueError("Either file or text is required.")

    if not file.filename:
        raise ValueError("Filename is missing.")

    extension = Path(file.filename).suffix.lower()
    saved_name = f"{uuid4().hex}{extension}"
    saved_path = INPUT_DIR / saved_name

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file.filename, parse_file(saved_path)


def _generate_testcases_from_source(
    *,
    file: UploadFile | None,
    text: str | None,
    perspectives: str,
    figma_url: str | None = None,
    figma_context: str | None = None,
):
    _, parsed_text = _load_extract_source(file=file, text=text)
    requirements = extract_requirements_from_text(parsed_text)
    figma_prompt_context = _load_figma_prompt_context(
        figma_url=figma_url,
        figma_context_text=figma_context,
    )
    policy_context = load_policy_context(parsed_text, figma_prompt_context).text
    analysis = analyze_requirements(requirements, policy_context=policy_context)
    return generate_testcases_from_requirements(
        requirements=requirements,
        perspectives=_parse_perspectives(perspectives),
        analysis=analysis,
        figma_context=figma_prompt_context,
        policy_context=policy_context,
    )


def _load_figma_prompt_context(
    *,
    figma_url: str | None,
    figma_context_text: str | None = None,
    include_images: bool = False,
) -> str:
    context = _load_figma_context(
        figma_url=figma_url,
        include_images=include_images,
    )
    return _build_figma_prompt_context(
        figma_context=context,
        figma_context_text=figma_context_text,
    )


def _build_figma_prompt_context(
    *,
    figma_context: FigmaContext | None,
    figma_context_text: str | None,
) -> str:
    parts: list[str] = []

    if figma_context_text and figma_context_text.strip():
        parts.append(figma_context_text.strip())

    if figma_context:
        parts.append(figma_context_to_prompt_text(figma_context))

    return "\n\n".join(parts)


def _load_figma_context(
    *,
    figma_url: str | None,
    include_images: bool = False,
) -> FigmaContext | None:
    if not figma_url or not figma_url.strip():
        return None

    return extract_figma_context(
        figma_url.strip(),
        include_images=include_images,
    )


def _parse_perspectives(perspectives: str) -> list[str]:
    parsed = [
        perspective.strip().upper()
        for perspective in perspectives.split(",")
        if perspective.strip()
    ]

    if not parsed:
        raise ValueError("At least one perspective is required.")

    return parsed


def _safe_export_filename(filename: str, extension: str) -> str:
    stem = Path(filename).stem or "testcases"
    safe_stem = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in stem
    ).strip("_")

    return f"{safe_stem or 'testcases'}.{extension}"
