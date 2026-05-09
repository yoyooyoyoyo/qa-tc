from __future__ import annotations

from datetime import datetime

from app.schemas.analysis import RequirementAnalysisResult, ScenarioGap


def analysis_to_gap_report_markdown(
    analysis: RequirementAnalysisResult,
    *,
    title: str = "기획서 누락/모호점 리포트",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "- 목적: 테스트케이스와 분리해 기획서에 보완되어야 할 누락/모호점/확인 질문을 정리한다.",
        "",
        "## 요약",
        "",
        f"- 누락/모호점: {len(analysis.gap_report)}건",
        f"- PM 확인 질문: {len(analysis.questions_for_pm)}건",
        f"- 정책 충돌: {len(analysis.policy_conflicts)}건",
        f"- 추론 기반 테스트 후보: {len(analysis.inferred_test_candidates)}건",
        "",
    ]

    lines.extend(_render_gap_report(analysis.gap_report))
    lines.extend(_render_string_section("기획자 확인 질문", analysis.questions_for_pm))
    lines.extend(_render_string_section("정책 충돌", analysis.policy_conflicts))
    lines.extend(_render_string_section("추론에 사용한 가정", analysis.assumptions))
    lines.extend(_render_string_section("추론 기반 테스트 후보", analysis.inferred_test_candidates))
    lines.extend(_render_string_section("누락된 정책", analysis.missing_policies))
    lines.extend(_render_string_section("테스트 불가 항목", analysis.untestable_items))

    return "\n".join(lines).rstrip() + "\n"


def _render_gap_report(gaps: list[ScenarioGap]) -> list[str]:
    lines = ["## 누락/모호점 리포트", ""]

    if not gaps:
        return lines + ["- 발견된 누락/모호점 없음", ""]

    for index, gap in enumerate(gaps, start=1):
        lines.extend(
            [
                f"### GAP-{index:03d} {gap.area or gap.requirement_id}",
                "",
                f"- requirement_id: `{gap.requirement_id}`",
                f"- gap_type: `{gap.gap_type}`",
                f"- severity: `{gap.severity}`",
                f"- scenario: {gap.scenario}",
                f"- issue: {gap.issue or gap.missing_detail}",
                f"- missing_detail: {gap.missing_detail}",
                f"- why_it_matters: {gap.why_it_matters or gap.risk}",
                f"- risk: {gap.risk}",
                f"- question_for_pm: {gap.question}",
                f"- suggested_test: {gap.suggested_test}",
                "",
            ]
        )

    return lines


def _render_string_section(title: str, values: list[str]) -> list[str]:
    lines = [f"## {title}", ""]

    if not values:
        return lines + ["- 없음", ""]

    lines.extend(f"- {value}" for value in values)
    lines.append("")
    return lines
