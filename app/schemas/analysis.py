from __future__ import annotations

from pydantic import BaseModel, Field


class PerspectiveAnalysis(BaseModel):
    perspective: str = Field(..., description="분석 관점: PM, DEV, QA")
    findings: list[str] = Field(default_factory=list, description="주요 발견 사항")
    risks: list[str] = Field(default_factory=list, description="테스트/구현 리스크")
    open_questions: list[str] = Field(default_factory=list, description="확인 필요 사항")


class RequirementAnalysisResult(BaseModel):
    analyses: list[PerspectiveAnalysis] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list, description="기획서 내 모순")
    missing_policies: list[str] = Field(default_factory=list, description="누락된 정책")
    untestable_items: list[str] = Field(default_factory=list, description="현재 문서만으로 테스트 불가한 항목")
