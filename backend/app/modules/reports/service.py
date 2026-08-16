from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.categories.contracts import category_path_map
from app.modules.operations.contracts import OperationType, ReportOperation, report_operations
from app.modules.reports.schemas import (
    IncomeExpenseReportResponse,
    IncomeExpenseReportType,
    ReportCategoryResponse,
    ReportOperationResponse,
)


def income_expense_report(
    session: Session,
    *,
    report_type: IncomeExpenseReportType,
    from_on: date,
    through_on: date,
) -> IncomeExpenseReportResponse:
    rows = report_operations(
        session,
        operation_type=OperationType(report_type.value),
        from_on=from_on,
        through_on=through_on,
    )
    paths = category_path_map(session)
    grouped: dict[UUID, list[ReportOperation]] = defaultdict(list)
    for row in rows:
        grouped[row.category_id].append(row)
    total = sum((row.amount for row in rows), Decimal(0))
    categories = []
    for category_id, operations in grouped.items():
        path = paths[category_id]
        amount = sum((operation.amount for operation in operations), Decimal(0))
        share = amount * 100 / total if total else Decimal(0)
        categories.append(
            ReportCategoryResponse(
                category_id=path.id,
                category_name=path.name,
                root_category_id=path.root_id,
                root_category_name=path.root_name,
                amount=_money(amount),
                share=format(share, ".2f"),
                operations=[
                    ReportOperationResponse(
                        id=operation.id,
                        occurred_on=operation.occurred_on,
                        description=operation.description,
                        amount=_money(operation.amount),
                    )
                    for operation in operations
                ],
            )
        )
    categories.sort(
        key=lambda item: (
            -Decimal(item.amount),
            item.root_category_name,
            item.category_name,
        )
    )
    return IncomeExpenseReportResponse(
        type=report_type,
        from_on=from_on,
        through_on=through_on,
        total_amount=_money(total),
        operation_count=len(rows),
        categories=categories,
    )


def _money(value: Decimal) -> str:
    return format(value, ".4f")
