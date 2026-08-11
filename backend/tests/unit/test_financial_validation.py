from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.application.accounts import calendar_date_at
from app.modules.accounts.schemas import AccountCreateRequest
from app.modules.funds.schemas import AllocationCreateRequest
from app.modules.funds.service import percentage_allocations
from app.modules.operations.schemas import OperationCreateRequest


def test_money_accepts_decimal_strings_without_binary_float() -> None:
    payload = AccountCreateRequest(type="cash", name="Wallet", initial_balance="10.2300")
    assert payload.initial_balance == Decimal("10.2300")


@pytest.mark.parametrize("value", [0.1, "NaN", "Infinity", "1.00001"])
def test_money_rejects_float_non_finite_and_excess_scale(value: object) -> None:
    with pytest.raises(ValidationError):
        AccountCreateRequest(type="cash", name="Wallet", initial_balance=value)


def test_operation_shapes_encode_posting_invariants() -> None:
    income = OperationCreateRequest(
        type="income",
        occurred_on="2026-08-02",
        amount="10.2300",
        account_id="10000000-0000-0000-0000-000000000001",
        category_id="20000000-0000-0000-0000-000000000001",
    )
    assert income.amount == Decimal("10.2300")

    adjustment = OperationCreateRequest(
        type="balance_adjustment",
        occurred_on="2026-08-02",
        amount="-1.5",
        account_id="10000000-0000-0000-0000-000000000001",
        reason="Bank reconciliation",
    )
    assert adjustment.amount == Decimal("-1.5")


@pytest.mark.parametrize(
    "payload",
    [
        {
            "type": "expense",
            "occurred_on": "2026-08-02",
            "amount": "1",
            "account_id": "10000000-0000-0000-0000-000000000001",
        },
        {
            "type": "transfer",
            "occurred_on": "2026-08-02",
            "amount": "1",
            "account_id": "10000000-0000-0000-0000-000000000001",
            "destination_account_id": "10000000-0000-0000-0000-000000000001",
        },
        {
            "type": "balance_adjustment",
            "occurred_on": "2026-08-02",
            "amount": "0",
            "account_id": "10000000-0000-0000-0000-000000000001",
            "reason": "Reconciliation",
        },
    ],
)
def test_operation_rejects_invalid_posting_shapes(payload: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        OperationCreateRequest.model_validate(payload)


def test_negative_initial_balance_is_rejected_until_overdraft_policy_is_defined() -> None:
    with pytest.raises(ValidationError):
        AccountCreateRequest(type="cash", name="Wallet", initial_balance="-1.0000")


def test_account_name_is_trimmed_and_must_not_be_blank() -> None:
    assert AccountCreateRequest(type="debit", name="  Card  ").name == "Card"
    with pytest.raises(ValidationError):
        AccountCreateRequest(type="cash", name="   ")


def test_financial_calendar_date_uses_application_timezone() -> None:
    instant = datetime(2026, 8, 1, 22, 30, tzinfo=UTC)
    assert str(calendar_date_at(instant, "Europe/Moscow")) == "2026-08-02"
    assert str(calendar_date_at(instant, "America/New_York")) == "2026-08-01"


def test_fund_percentage_rounding_is_exact_independent_and_reproducible() -> None:
    first = UUID("10000000-0000-0000-0000-000000000001")
    second = UUID("20000000-0000-0000-0000-000000000001")
    percentages = [(first, Decimal("33.3333")), (second, Decimal("20"))]

    forward = percentage_allocations(Decimal("10"), percentages)
    reverse = percentage_allocations(Decimal("10"), list(reversed(percentages)))

    assert {item.fund_id: item.amount for item in forward} == {
        first: Decimal("3.3333"),
        second: Decimal("2.0000"),
    }
    assert {item.fund_id: item.amount for item in reverse} == {
        item.fund_id: item.amount for item in forward
    }


@pytest.mark.parametrize(
    "allocations", [[], [{"fund_id": "10000000-0000-0000-0000-000000000001", "amount": "0"}]]
)
def test_allocation_rejects_empty_or_noop_movements(allocations: list[dict[str, str]]) -> None:
    with pytest.raises(ValidationError):
        AllocationCreateRequest.model_validate(
            {
                "account_id": "10000000-0000-0000-0000-000000000002",
                "amount": "10",
                "occurred_on": "2026-08-11",
                "allocations": allocations,
            }
        )
