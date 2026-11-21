"""Comandos do administrador. O grupo de origem não entra aqui."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from frota_plus.domain.dates import read_operation_date
from frota_plus.domain.money import parse_amount

AMOUNT = r"([0-9]+(?:[.,][0-9]{1,2})?)"
OPTIONAL_DATE = rf"(?:\s+data\s*=\s*(\d{{1,2}}/\d{{1,2}}(?:/\d{{4}})?))?"
FUEL_COMMAND = re.compile(rf"^/ajustar\s+combustivel\s*=\s*{AMOUNT}{OPTIONAL_DATE}\s*$", re.I)
PNR_COMMAND = re.compile(rf"^/pnr\s+{AMOUNT}{OPTIONAL_DATE}\s*$", re.I)
MAINTENANCE_COMMAND = re.compile(
    rf'^/manuten[cç][aã]o\s+"([^"]+)"\s+{AMOUNT}{OPTIONAL_DATE}\s*$',
    re.I,
)
HELP_COMMAND = re.compile(r"^/ajuda\s*$", re.I)
RETRY_COMMAND = re.compile(r"^/retry\s*$", re.I)


@dataclass(frozen=True)
class FuelCommand:
    amount: Decimal
    operation: date | None
    needs_confirmation: bool


@dataclass(frozen=True)
class PnrCommand:
    amount: Decimal
    operation: date | None
    needs_confirmation: bool


@dataclass(frozen=True)
class MaintenanceCommand:
    description: str
    amount: Decimal
    operation: date | None
    needs_confirmation: bool


@dataclass(frozen=True)
class HelpCommand:
    pass


@dataclass(frozen=True)
class RetryCommand:
    pass


def _resolve_date(raw: str | None, today: date) -> tuple[date | None, bool]:
    if not raw:
        return None, False
    read = read_operation_date(raw, today)
    return read.operation, read.needs_confirmation


def parse_command(
    text: str, today: date
) -> FuelCommand | PnrCommand | MaintenanceCommand | HelpCommand | RetryCommand | None:
    stripped = (text or "").strip()
    if HELP_COMMAND.match(stripped):
        return HelpCommand()
    if RETRY_COMMAND.match(stripped):
        return RetryCommand()
    fuel = FUEL_COMMAND.match(stripped)
    if fuel:
        operation, pending = _resolve_date(fuel.group(2), today)
        return FuelCommand(parse_amount(fuel.group(1)), operation, pending)
    pnr = PNR_COMMAND.match(stripped)
    if pnr:
        operation, pending = _resolve_date(pnr.group(2), today)
        return PnrCommand(parse_amount(pnr.group(1)), operation, pending)
    maintenance = MAINTENANCE_COMMAND.match(stripped)
    if maintenance:
        operation, pending = _resolve_date(maintenance.group(3), today)
        return MaintenanceCommand(
            maintenance.group(1).strip(),
            parse_amount(maintenance.group(2)),
            operation,
            pending,
        )
    return None
