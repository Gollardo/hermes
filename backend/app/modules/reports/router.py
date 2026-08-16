from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.database import DatabaseSession
from app.modules.reports.schemas import IncomeExpenseReportResponse, IncomeExpenseReportType
from app.modules.reports.service import income_expense_report

read_router = APIRouter(prefix="/reports", tags=["reports"])


@read_router.get("/income-expense", response_model=IncomeExpenseReportResponse)
def read_income_expense_report(
    session: DatabaseSession,
    type: IncomeExpenseReportType,
    from_on: date,
    through_on: date,
) -> IncomeExpenseReportResponse:
    if through_on < from_on:
        raise HTTPException(422, detail={"code": "invalid_period", "message": "Invalid period"})
    return income_expense_report(
        session,
        report_type=type,
        from_on=from_on,
        through_on=through_on,
    )
