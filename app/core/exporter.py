from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Iterable

from app.schemas.testcase import TestCase


TESTCASE_EXPORT_HEADERS = [
    "testcase_id",
    "requirement_id",
    "perspective",
    "priority",
    "test_type",
    "title",
    "preconditions",
    "steps",
    "test_data",
    "expected_result",
    "notes",
]


def testcases_to_tsv(testcases: Iterable[TestCase]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=TESTCASE_EXPORT_HEADERS,
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()

    for testcase in testcases:
        writer.writerow(_flatten_testcase(testcase))

    return output.getvalue()


def testcases_to_xlsx(testcases: Iterable[TestCase]) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required for xlsx export.") from exc

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "testcases"
    worksheet.append(TESTCASE_EXPORT_HEADERS)

    for testcase in testcases:
        row = _flatten_testcase(testcase)
        worksheet.append([row[header] for header in TESTCASE_EXPORT_HEADERS])

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def _flatten_testcase(testcase: TestCase) -> dict[str, str]:
    return {
        "testcase_id": testcase.testcase_id,
        "requirement_id": testcase.requirement_id,
        "perspective": testcase.perspective,
        "priority": testcase.priority,
        "test_type": testcase.test_type,
        "title": testcase.title,
        "preconditions": "\n".join(testcase.preconditions),
        "steps": "\n".join(testcase.steps),
        "test_data": testcase.test_data,
        "expected_result": testcase.expected_result,
        "notes": testcase.notes,
    }
