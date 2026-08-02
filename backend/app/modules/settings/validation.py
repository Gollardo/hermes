import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")


def normalize_currency(value: str) -> str:
    normalized = value.strip().upper()
    if not _CURRENCY_CODE.fullmatch(normalized):
        raise ValueError("Currency must be a three-letter ISO 4217 code")
    return normalized


def normalize_timezone(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 64:
        raise ValueError("Timezone must be a valid IANA identifier")
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as error:
        raise ValueError("Timezone must be a valid IANA identifier") from error
    return normalized
