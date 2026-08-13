from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.scheduling.models import RecurrenceFrequency
from app.modules.scheduling.schemas import RecurringRuleCreateRequest
from app.modules.scheduling.service import calendar_year_later, recurrence_dates

ACCOUNT = "10000000-0000-0000-0000-000000000001"
DESTINATION = "10000000-0000-0000-0000-000000000002"
CATEGORY = "20000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize(
    ("frequency", "anchor", "range_from", "range_to", "expected"),
    [
        (
            RecurrenceFrequency.DAILY,
            date(2026, 8, 10),
            date(2026, 8, 11),
            date(2026, 8, 13),
            [date(2026, 8, 11), date(2026, 8, 12), date(2026, 8, 13)],
        ),
        (
            RecurrenceFrequency.WEEKLY,
            date(2026, 8, 3),
            date(2026, 8, 11),
            date(2026, 8, 31),
            [date(2026, 8, 17), date(2026, 8, 24), date(2026, 8, 31)],
        ),
        (
            RecurrenceFrequency.MONTHLY,
            date(2026, 1, 15),
            date(2026, 3, 16),
            date(2026, 6, 15),
            [date(2026, 4, 15), date(2026, 5, 15), date(2026, 6, 15)],
        ),
        (
            RecurrenceFrequency.YEARLY,
            date(2020, 5, 20),
            date(2026, 5, 21),
            date(2028, 5, 20),
            [date(2027, 5, 20), date(2028, 5, 20)],
        ),
    ],
)
def test_recurrence_dates_are_anchored_and_bounded(
    frequency: RecurrenceFrequency,
    anchor: date,
    range_from: date,
    range_to: date,
    expected: list[date],
) -> None:
    assert (
        recurrence_dates(
            frequency=frequency,
            anchor=anchor,
            range_from=range_from,
            range_to=range_to,
            end_on=None,
        )
        == expected
    )


def test_recurrence_respects_inclusive_end_and_calendar_year_horizon() -> None:
    assert calendar_year_later(date(2024, 2, 29)) == date(2025, 2, 28)
    assert recurrence_dates(
        frequency=RecurrenceFrequency.MONTHLY,
        anchor=date(2026, 1, 10),
        range_from=date(2026, 2, 1),
        range_to=date(2026, 6, 1),
        end_on=date(2026, 4, 10),
    ) == [date(2026, 2, 10), date(2026, 3, 10), date(2026, 4, 10)]


def test_daily_horizon_including_leap_day_contains_367_dates() -> None:
    dates = recurrence_dates(
        frequency=RecurrenceFrequency.DAILY,
        anchor=date(2023, 3, 1),
        range_from=date(2023, 3, 1),
        range_to=calendar_year_later(date(2023, 3, 1)),
        end_on=None,
    )

    assert len(dates) == 367
    assert dates[-1] == date(2024, 3, 1)


def test_weekly_weekdays_and_interval_are_deterministic() -> None:
    assert recurrence_dates(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=2,
        weekdays=[1, 5],
        anchor=date(2026, 8, 3),
        range_from=date(2026, 8, 3),
        range_to=date(2026, 8, 31),
        end_on=None,
    ) == [
        date(2026, 8, 3),
        date(2026, 8, 7),
        date(2026, 8, 17),
        date(2026, 8, 21),
        date(2026, 8, 31),
    ]


def test_monthly_interval_uses_anchor_day() -> None:
    assert recurrence_dates(
        frequency=RecurrenceFrequency.MONTHLY,
        interval=3,
        anchor=date(2026, 1, 12),
        range_from=date(2026, 1, 1),
        range_to=date(2026, 10, 12),
        end_on=None,
    ) == [date(2026, 1, 12), date(2026, 4, 12), date(2026, 7, 12), date(2026, 10, 12)]


def test_weekly_rule_requires_unique_valid_weekdays() -> None:
    with pytest.raises(ValidationError):
        RecurringRuleCreateRequest(
            type="income",
            frequency="weekly",
            interval=2,
            weekdays=[1, 1],
            start_on="2026-08-03",
            amount="10",
            account_id=ACCOUNT,
            category_id=CATEGORY,
        )


def test_recurring_rule_shape_and_exact_money() -> None:
    rule = RecurringRuleCreateRequest(
        type="transfer",
        frequency="monthly",
        start_on="2026-08-15",
        amount="1250.2300",
        account_id=ACCOUNT,
        destination_account_id=DESTINATION,
    )
    assert rule.amount == Decimal("1250.2300")


@pytest.mark.parametrize(
    "payload",
    [
        {
            "type": "income",
            "frequency": "monthly",
            "start_on": "2026-01-29",
            "amount": "1",
            "account_id": ACCOUNT,
            "category_id": CATEGORY,
        },
        {
            "type": "expense",
            "frequency": "yearly",
            "start_on": "2028-02-29",
            "amount": "1",
            "account_id": ACCOUNT,
            "category_id": CATEGORY,
        },
        {
            "type": "income",
            "frequency": "daily",
            "start_on": "2026-08-11",
            "end_on": "2026-08-10",
            "amount": "1",
            "account_id": ACCOUNT,
            "category_id": CATEGORY,
        },
        {
            "type": "transfer",
            "frequency": "weekly",
            "start_on": "2026-08-11",
            "amount": "1",
            "account_id": ACCOUNT,
            "destination_account_id": ACCOUNT,
        },
        {
            "type": "income",
            "frequency": "daily",
            "start_on": "2026-08-11",
            "amount": 0.1,
            "account_id": ACCOUNT,
            "category_id": CATEGORY,
        },
    ],
)
def test_recurring_rule_rejects_ambiguous_or_invalid_shape(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        RecurringRuleCreateRequest.model_validate(payload)
