from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.accounts.schemas import AccountCreateRequest


def test_money_accepts_decimal_strings_without_binary_float() -> None:
    payload = AccountCreateRequest(type="cash", name="Wallet", initial_balance="10.2300")
    assert payload.initial_balance == Decimal("10.2300")


@pytest.mark.parametrize("value", [0.1, "NaN", "Infinity", "1.00001"])
def test_money_rejects_float_non_finite_and_excess_scale(value: object) -> None:
    with pytest.raises(ValidationError):
        AccountCreateRequest(type="cash", name="Wallet", initial_balance=value)


def test_negative_initial_balance_is_rejected_until_overdraft_policy_is_defined() -> None:
    with pytest.raises(ValidationError):
        AccountCreateRequest(type="cash", name="Wallet", initial_balance="-1.0000")


def test_account_name_is_trimmed_and_must_not_be_blank() -> None:
    assert AccountCreateRequest(type="debit", name="  Card  ").name == "Card"
    with pytest.raises(ValidationError):
        AccountCreateRequest(type="cash", name="   ")
