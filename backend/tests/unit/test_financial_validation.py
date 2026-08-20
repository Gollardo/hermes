from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.application.accounts import calendar_date_at
from app.modules.accounts.schemas import AccountCreateRequest
from app.modules.funds.schemas import AllocationCreateRequest
from app.modules.funds.service import (
    FundDistributionState,
    complete_percentage_allocations,
    dynamic_percentages,
    percentage_allocations,
)
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


def test_dynamic_percentages_apply_minimum_weights_and_exclude_filled_funds() -> None:
    ids = [UUID(f"10000000-0000-0000-0000-{index:012d}") for index in range(1, 8)]
    states = [
        FundDistributionState(ids[0], Decimal("80"), Decimal("100")),
        FundDistributionState(ids[1], Decimal("84"), Decimal("100")),
        FundDistributionState(ids[2], Decimal("84"), Decimal("100")),
        FundDistributionState(ids[3], Decimal("84"), Decimal("100")),
        FundDistributionState(ids[4], Decimal("84"), Decimal("100")),
        FundDistributionState(ids[5], Decimal("84"), Decimal("100")),
        FundDistributionState(ids[6], Decimal("100"), Decimal("100")),
    ]

    percentages = dict(dynamic_percentages(states))

    assert percentages[ids[0]] == Decimal("19.0000")
    assert ids[6] not in percentages
    assert sum(percentages.values()) == Decimal("100.0000")
    assert all(value >= Decimal("5") for value in percentages.values())


def test_dynamic_percentages_compare_relative_progress_not_target_size() -> None:
    first = UUID("11000000-0000-0000-0000-000000000001")
    second = UUID("11000000-0000-0000-0000-000000000002")

    equal_progress = dict(
        dynamic_percentages(
            [
                FundDistributionState(first, Decimal("50"), Decimal("100")),
                FundDistributionState(second, Decimal("500"), Decimal("1000")),
            ]
        )
    )
    lower_progress = dict(
        dynamic_percentages(
            [
                FundDistributionState(first, Decimal("0"), Decimal("100")),
                FundDistributionState(second, Decimal("500"), Decimal("1000")),
            ]
        )
    )

    assert equal_progress == {first: Decimal("50.0000"), second: Decimal("50.0000")}
    assert lower_progress == {first: Decimal("65.0000"), second: Decimal("35.0000")}


@pytest.mark.parametrize("count", [1, 20, 21, 25])
def test_dynamic_percentages_are_exact_for_any_active_count(count: int) -> None:
    states = [
        FundDistributionState(
            UUID(f"20000000-0000-0000-0000-{index:012d}"), Decimal(0), Decimal(100)
        )
        for index in range(1, count + 1)
    ]
    percentages = dynamic_percentages(states)

    assert len(percentages) == count
    assert sum((percentage for _, percentage in percentages), Decimal(0)) == Decimal("100.0000")
    if count == 20:
        assert {percentage for _, percentage in percentages} == {Decimal("5.0000")}
    if count == 25:
        assert {percentage for _, percentage in percentages} == {Decimal("4.0000")}


def test_dynamic_percentages_use_only_the_equal_base_when_more_than_twenty_are_active() -> None:
    states = [
        FundDistributionState(
            UUID(f"21000000-0000-0000-0000-{index:012d}"),
            Decimal(index),
            Decimal("100"),
        )
        for index in range(1, 22)
    ]

    percentages = [percentage for _, percentage in dynamic_percentages(states)]

    assert max(percentages) - min(percentages) == Decimal("0.0001")
    assert sum(percentages, Decimal(0)) == Decimal("100.0000")


def test_dynamic_money_rounding_distributes_the_complete_incoming_amount() -> None:
    ids = [
        UUID("30000000-0000-0000-0000-000000000001"),
        UUID("30000000-0000-0000-0000-000000000002"),
        UUID("30000000-0000-0000-0000-000000000003"),
    ]
    allocations = complete_percentage_allocations(
        Decimal("10.0000"),
        [(ids[0], Decimal("33.3334")), (ids[1], Decimal("33.3333")), (ids[2], Decimal("33.3333"))],
    )

    assert sum((item.amount for item in allocations), Decimal(0)) == Decimal("10.0000")
    assert {item.amount for item in allocations} == {Decimal("3.3333"), Decimal("3.3334")}


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
