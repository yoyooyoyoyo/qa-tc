from __future__ import annotations

from pydantic import BaseModel, Field


class PerspectiveAnalysis(BaseModel):
    perspective: str = Field(..., description="분석 관점: PM, DEV, QA")
    findings: list[str] = Field(default_factory=list, description="주요 발견 사항")
    risks: list[str] = Field(default_factory=list, description="테스트/구현 리스크")
    open_questions: list[str] = Field(default_factory=list, description="확인 필요 사항")


class RequirementFocus(BaseModel):
    requirement_id: str = Field(..., description="연결된 요구사항 ID")
    is_core: bool = Field(default=False, description="핵심 기능 여부")
    focus_score: int = Field(default=0, description="핵심도 점수: 0~100")
    focus_reason: list[str] = Field(default_factory=list, description="핵심/비핵심 판단 사유")
    recommended_depth: str = Field(
        default="smoke",
        description="권장 생성 깊이: deep, smoke, omit",
    )


class ScenarioGap(BaseModel):
    requirement_id: str = Field(..., description="연결된 요구사항 ID")
    gap_type: str = Field(default="scenario_hole", description="누락 유형")
    area: str = Field(default="", description="영향 영역")
    scenario: str = Field(..., description="누락이 발견된 사용자/운영 시나리오")
    issue: str = Field(default="", description="누락/모호점 요약")
    missing_detail: str = Field(..., description="기획서에 누락되었거나 불명확한 내용")
    why_it_matters: str = Field(default="", description="왜 중요한지")
    risk: str = Field(default="", description="누락 시 발생 가능한 리스크")
    question: str = Field(default="", description="기획자/개발자에게 확인할 질문")
    suggested_test: str = Field(default="", description="추론 기반 테스트 후보")
    severity: str = Field(default="Medium", description="High, Medium, Low")


class RequirementAnalysisResult(BaseModel):
    analyses: list[PerspectiveAnalysis] = Field(default_factory=list)
    requirement_focus: list[RequirementFocus] = Field(default_factory=list)
    scenario_gaps: list[ScenarioGap] = Field(default_factory=list)
    gap_report: list[ScenarioGap] = Field(default_factory=list)
    questions_for_pm: list[str] = Field(default_factory=list)
    policy_conflicts: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    inferred_test_candidates: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list, description="기획서 내 모순")
    missing_policies: list[str] = Field(default_factory=list, description="누락된 정책")
    untestable_items: list[str] = Field(default_factory=list, description="현재 문서만으로 테스트 불가한 항목")


class ExportGapReportRequest(BaseModel):
    analysis: RequirementAnalysisResult
    title: str = Field(default="기획서 누락/모호점 리포트")
