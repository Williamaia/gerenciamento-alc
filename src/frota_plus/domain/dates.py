"""A data da escala é a data escrita no texto, sem frase obrigatória."""

import re
from datetime import date, datetime, timedelta, timezone

DATE_PATTERN = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
SAO_PAULO = timezone(timedelta(hours=-3))


def sao_paulo_today(now: datetime | None = None) -> date:
    moment = now or datetime.now(SAO_PAULO)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=SAO_PAULO)
    return moment.astimezone(SAO_PAULO).date()


class DateRead:
    def __init__(self, operation: date | None, needs_confirmation: bool) -> None:
        self.operation = operation
        self.needs_confirmation = needs_confirmation


def read_operation_date(text: str, received_on: date) -> DateRead:
    found = DATE_PATTERN.findall(text or "")
    if len(found) != 1:
        return DateRead(None, True)
    day_text, month_text, year_text = found[0]
    day = int(day_text)
    month = int(month_text)
    if year_text:
        year = int(year_text)
        if year < 100:
            year += 2000
    else:
        year = received_on.year
    try:
        operation = date(year, month, day)
    except ValueError:
        return DateRead(None, True)
    if not year_text and operation - received_on > timedelta(days=7):
        return DateRead(operation, True)
    return DateRead(operation, False)
