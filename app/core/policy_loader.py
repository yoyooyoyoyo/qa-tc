from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
POLICY_DIR = BASE_DIR / "docs" / "policies"

GLOBAL_POLICY_FILES = [
    POLICY_DIR / "global" / "qa_policy.md",
    POLICY_DIR / "global" / "focus_policy.md",
    POLICY_DIR / "global" / "testcase_style_guide.md",
    POLICY_DIR / "global" / "defect_policy.md",
    POLICY_DIR / "global" / "release_checklist.md",
]

DOMAIN_POLICY_FILES = [
    POLICY_DIR / "domain" / "domain_terms.md",
]

DOMAIN_POLICY_KEYWORDS = {
    POLICY_DIR / "domain" / "coupon_policy.md": [
        "coupon",
        "쿠폰",
        "할인",
        "다운로드쿠폰",
        "코드쿠폰",
        "쿠폰적용가",
    ],
    POLICY_DIR / "domain" / "booking_policy.md": [
        "booking",
        "reservation",
        "예약",
        "예약확정",
        "확정대기",
        "검진예약",
        "예약취소",
    ],
    POLICY_DIR / "domain" / "payment_policy.md": [
        "payment",
        "price",
        "결제",
        "가격",
        "금액",
        "부가세",
        "케어비",
        "영수증",
        "지원금",
        "검진지원금",
    ],
    POLICY_DIR / "domain" / "booking_history_policy.md": [
        "booking history",
        "예약내역",
        "내정보",
        "결제 영수증",
        "검진완료",
        "미수검",
        "취소완료",
    ],
}

FEATURE_POLICY_KEYWORDS = {
    POLICY_DIR / "pms_v20_ai_opinion_policy_notes.md": [
        "pms",
        "종합소견",
        "ai 소견",
        "소견생성",
        "소견확정",
        "추적관찰",
        "보고서",
        "발송대기",
        "발송성공",
        "발송실패",
        "발송취소",
        "과금",
    ],
    POLICY_DIR / "feature" / "app_v20_coupon_booking_policy_notes.md": [
        "coupon",
        "쿠폰",
        "할인",
        "다운로드쿠폰",
        "코드쿠폰",
        "쿠폰적용가",
        "멤버십",
    ],
    POLICY_DIR / "feature" / "booking_history_policy_notes.md": [
        "booking",
        "reservation",
        "예약",
        "예약내역",
        "결제",
        "영수증",
        "지원금",
        "검진지원금",
        "예약확정",
        "확정대기",
    ],
}


@dataclass(frozen=True)
class PolicyContext:
    text: str
    loaded_files: list[str]


def load_policy_context(*context_hints: str) -> PolicyContext:
    """Load global policies, shared terms, and keyword-matched domain/feature policies."""
    hint_text = "\n".join(hint for hint in context_hints if hint).lower()

    selected_files: list[Path] = []
    selected_files.extend(GLOBAL_POLICY_FILES)
    selected_files.extend(DOMAIN_POLICY_FILES)

    for path, keywords in DOMAIN_POLICY_KEYWORDS.items():
        if any(keyword.lower() in hint_text for keyword in keywords):
            selected_files.append(path)

    for path, keywords in FEATURE_POLICY_KEYWORDS.items():
        if any(keyword.lower() in hint_text for keyword in keywords):
            selected_files.append(path)

    existing_files = _dedupe_existing_files(selected_files)
    sections = [_format_policy_file(path) for path in existing_files]

    return PolicyContext(
        text="\n\n".join(section for section in sections if section),
        loaded_files=[_relative_policy_path(path) for path in existing_files],
    )


def _dedupe_existing_files(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []

    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        result.append(path)

    return result


def _format_policy_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return ""

    return f"[Policy: {_relative_policy_path(path)}]\n{content}"


def _relative_policy_path(path: Path) -> str:
    return str(path.relative_to(BASE_DIR))
