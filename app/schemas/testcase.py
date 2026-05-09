from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.requirement import Requirement
from app.schemas.analysis import RequirementAnalysisResult
from app.schemas.figma import FigmaContext


class TestCase(BaseModel):
    testcase_id: str = Field(..., description="테스트케이스 식별자")
    requirement_id: str = Field(..., description="연결된 요구사항 ID")
    perspective: str = Field(..., description="작성 관점: PM, DEV, QA")
    priority: str = Field(..., description="우선순위: High, Medium, Low")
    test_type: str = Field(..., description="테스트 유형")
    title: str = Field(..., description="테스트 제목")
    test_screen: str = Field(default="", description="테스트 진행 화면")
    preconditions: list[str] = Field(default_factory=list, description="사전 조건")
    steps: list[str] = Field(default_factory=list, description="테스트 절차")
    test_data: str = Field(default="", description="테스트 데이터")
    expected_result: str = Field(..., description="기대 결과")
    notes: str = Field(default="", description="비고")
    category: str = Field(default="Functional", description="정상/예외/경계값/권한/상태전이/API/회귀 등")
    severity: str = Field(default="Medium", description="장애 영향도: Critical, Major, Minor")
    automation_candidate: bool = Field(default=False, description="자동화 후보 여부")
    related_risks: list[str] = Field(default_factory=list, description="관련 리스크")
    traceability: list[str] = Field(default_factory=list, description="요구사항/정책 근거")
    source_quote: str = Field(default="", description="테스트케이스 근거 원문")
    source_policy: list[str] = Field(default_factory=list, description="참고한 정책 문서")
    related_policy: list[str] = Field(default_factory=list, description="관련 정책/규칙")
    generation_scope: str = Field(
        default="core-deep",
        description="생성 범위: core-deep, smoke-only, omitted",
    )
    risk_basis: list[str] = Field(
        default_factory=list,
        description="리스크 근거: business, data, state, auth, api 등",
    )
    omit_reason: str = Field(default="", description="축약/제외 사유")
    quality_warnings: list[str] = Field(default_factory=list, description="후처리 품질 경고")


class TestCaseGenerationRequest(BaseModel):
    requirements: list[Requirement]
    perspectives: list[str] = Field(
        default_factory=lambda: ["PM", "DEV", "QA"],
        description="테스트케이스 생성 관점",
    )


class TestCaseGenerationResult(BaseModel):
    testcases: list[TestCase] = Field(default_factory=list)


class GenerateTestCasesResponse(BaseModel):
    message: str
    requirement_count: int
    testcase_count: int
    analysis: RequirementAnalysisResult = Field(default_factory=RequirementAnalysisResult)
    testcases: list[TestCase]


class GenerateTestCasesFromDocumentResponse(BaseModel):
    message: str
    filename: str
    text_length: int
    requirement_count: int
    testcase_count: int
    analysis: RequirementAnalysisResult = Field(default_factory=RequirementAnalysisResult)
    figma_context: FigmaContext | None = None
    requirements: list[Requirement]
    testcases: list[TestCase]


class ExportTestCasesRequest(BaseModel):
    testcases: list[TestCase]
    filename: str = Field(default="testcases", description="확장자를 제외한 다운로드 파일명")
