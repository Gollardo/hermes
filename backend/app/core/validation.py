from decimal import Decimal, InvalidOperation
from typing import Annotated

from pydantic import BeforeValidator


def parse_decimal(value: object, *, scale: int, maximum: Decimal) -> Decimal:
    if isinstance(value, float):
        raise ValueError("binary floating-point values are not accepted")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("invalid decimal value") from error
    exponent = result.as_tuple().exponent
    if (
        not result.is_finite()
        or not isinstance(exponent, int)
        or exponent < -scale
        or abs(result) > maximum
    ):
        raise ValueError(f"value must have at most {scale} decimal places")
    return result


def parse_money(value: object) -> Decimal:
    return parse_decimal(value, scale=4, maximum=Decimal("9999999999999999.9999"))


Money = Annotated[Decimal, BeforeValidator(parse_money)]
