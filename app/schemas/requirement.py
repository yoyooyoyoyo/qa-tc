from __future__ import annotations

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    feature_id: str = Field(..., description="요구사항 식별자")
    feature_name: str = Field(..., description="기능명")
    platform: list[str] = Field(default_factory=list, description="적용 플랫폼")
    actor: str = Field(default="", description="행위자")
    entry_point: str = Field(default="", description="진입 경로")
    preconditions: list[str] = Field(default_factory=list, description="사전 조건")
    business_rules: list[str] = Field(default_factory=list, description="비즈니스 규칙")
    states: list[str] = Field(default_factory=list, description="상태값")
    dependencies: list[str] = Field(default_factory=list, description="의존 요소")
    open_questions: list[str] = Field(default_factory=list, description="확인 필요 사항")
    source_section: str = Field(default="", description="원문 내 섹션명")
    source_quote: str = Field(default="", description="요구사항 근거가 되는 원문 인용")
    confidence: float = Field(default=0.0, description="요구사항 추출 신뢰도")
    evidence: list[str] = Field(default_factory=list, description="요구사항 근거 목록")


class RequirementExtractionResult(BaseModel):
    requirements: list[Requirement] = Field(
        default_factory=list,
        description="기획서에서 추출한 테스트 가능 요구사항 목록",
    )


class ExtractRequirementsResponse(BaseModel):
    message: str
    filename: str
    text_length: int
    requirement_count: int
    requirements: list[Requirement]
