from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.requirement import Requirement


class TestCase(BaseModel):
    testcase_id: str = Field(..., description="테스트케이스 식별자")
    requirement_id: str = Field(..., description="연결된 요구사항 ID")
    perspective: str = Field(..., description="작성 관점: PM, DEV, QA")
    priority: str = Field(..., description="우선순위: High, Medium, Low")
    test_type: str = Field(..., description="테스트 유형")
    title: str = Field(..., description="테스트 제목")
    preconditions: list[str] = Field(default_factory=list, description="사전 조건")
    steps: list[str] = Field(default_factory=list, description="테스트 절차")
    test_data: str = Field(default="", description="테스트 데이터")
    expected_result: str = Field(..., description="기대 결과")
    notes: str = Field(default="", description="비고")


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
    testcases: list[TestCase]


class GenerateTestCasesFromDocumentResponse(BaseModel):
    message: str
    filename: str
    text_length: int
    requirement_count: int
    testcase_count: int
    requirements: list[Requirement]
    testcases: list[TestCase]


class ExportTestCasesRequest(BaseModel):
    testcases: list[TestCase]
    filename: str = Field(default="testcases", description="확장자를 제외한 다운로드 파일명")
