from __future__ import annotations

from app.schemas.requirement import Requirement
from app.schemas.testcase import TestCase


def improve_testcase_quality(
    testcases: list[TestCase],
    requirements: list[Requirement],
) -> list[TestCase]:
    requirement_by_id = {requirement.feature_id: requirement for requirement in requirements}
    improved: list[TestCase] = []
    seen: set[tuple[str, str, str, str]] = set()

    for testcase in testcases:
        requirement = requirement_by_id.get(testcase.requirement_id)
        warnings = list(testcase.quality_warnings)

        if requirement is None:
            warnings.append("연결된 requirement_id를 찾을 수 없음")
        else:
            testcase = _fill_traceability(testcase, requirement)

        if not testcase.steps:
            warnings.append("테스트 절차가 비어 있음")

        if _is_weak_expected_result(testcase.expected_result):
            warnings.append("기대 결과가 추상적이어서 구체화 필요")

        dedupe_key = (
            testcase.requirement_id,
            testcase.perspective,
            testcase.title.strip(),
            testcase.expected_result.strip(),
        )
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        testcase.quality_warnings = _dedupe_strings(warnings)
        improved.append(testcase)

    return _renumber_testcases(improved)


def _fill_traceability(testcase: TestCase, requirement: Requirement) -> TestCase:
    traceability = list(testcase.traceability)

    if requirement.feature_id not in traceability:
        traceability.insert(0, requirement.feature_id)

    for evidence in requirement.evidence[:3]:
        if evidence and evidence not in traceability:
            traceability.append(evidence)

    if not testcase.source_quote:
        testcase.source_quote = requirement.source_quote

    if requirement.open_questions and "확인 필요" not in testcase.notes:
        open_questions = " / ".join(requirement.open_questions)
        testcase.notes = f"{testcase.notes} 확인 필요: {open_questions}".strip()

    return testcase


def _is_weak_expected_result(expected_result: str) -> bool:
    weak_phrases = ["정상 동작", "요구사항에 맞게", "문제없이", "확인된다"]
    stripped = expected_result.strip()

    if len(stripped) < 12:
        return True

    return any(phrase in stripped for phrase in weak_phrases)


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)

    return deduped


def _renumber_testcases(testcases: list[TestCase]) -> list[TestCase]:
    for idx, testcase in enumerate(testcases, start=1):
        testcase.testcase_id = f"TC-{idx:03d}"

    return testcases
