from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from app.modules.categories.contracts import CategoryPath
from app.modules.operations.contracts import ReportOperation
from app.modules.reports.schemas import IncomeExpenseReportType
from app.modules.reports.service import income_expense_report


def test_report_groups_exact_amounts_and_orders_largest_category_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    food = UUID("10000000-0000-0000-0000-000000000001")
    travel = UUID("10000000-0000-0000-0000-000000000002")
    root = UUID("10000000-0000-0000-0000-000000000003")
    rows = [
        ReportOperation(UUID(int=1), date(2026, 8, 2), "Кофе", food, Decimal("0.1000")),
        ReportOperation(UUID(int=2), date(2026, 8, 3), "Обед", food, Decimal("0.2000")),
        ReportOperation(UUID(int=3), date(2026, 8, 4), None, travel, Decimal("10.0000")),
    ]
    monkeypatch.setattr(
        "app.modules.reports.service.report_operations", lambda *args, **kwargs: rows
    )
    monkeypatch.setattr(
        "app.modules.reports.service.category_path_map",
        lambda session: {
            food: CategoryPath(food, "Еда", root, "Повседневное"),
            travel: CategoryPath(travel, "Поездки", travel, "Поездки"),
        },
    )

    report = income_expense_report(
        object(),  # type: ignore[arg-type]
        report_type=IncomeExpenseReportType.EXPENSE,
        from_on=date(2026, 8, 1),
        through_on=date(2026, 8, 31),
    )

    assert report.total_amount == "10.3000"
    assert report.operation_count == 3
    assert [category.category_name for category in report.categories] == ["Поездки", "Еда"]
    assert report.categories[1].amount == "0.3000"
    assert report.categories[1].share == "2.91"
