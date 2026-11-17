"""Orquestra o dia: escala, paradas, comandos e parecer."""

import calendar
import logging
import re
from datetime import date, datetime
from decimal import Decimal

from frota_plus.commands import FuelCommand, MaintenanceCommand, PnrCommand, parse_command
from frota_plus.config import Settings
from frota_plus.domain.dates import SAO_PAULO, read_operation_date, sao_paulo_today
from frota_plus.domain.money import brl, driver_pay
from frota_plus.outbound import Outbound
from frota_plus.phones import same_phone
from frota_plus.domain.money import freight_for_km, stop_bonus, training_bonus
from frota_plus.routing import DistanceBook, fetch_road_leg
from frota_plus.reports import (
    daily_parecer,
    maintenance_only,
    quinzena_driver,
    quinzena_fiorino,
    stops_request,
    unreadable_scale,
)
from frota_plus.store import Store

logger = logging.getLogger("frota_plus.service")
INTEGERS = re.compile(r"\d+")


class DailyService:
    def __init__(self, settings: Settings, store: Store, outbound: Outbound, interpreter, distances=None) -> None:
        self.settings = settings
        self.store = store
        self.outbound = outbound
        self.interpreter = interpreter
        self.distances = distances or DistanceBook(store, fetch_road_leg)

    def handle(self, payload: dict, now: datetime | None = None) -> None:
        moment = now or datetime.now(SAO_PAULO)
        if payload.get("event") and not _is_upsert(str(payload.get("event"))):
            return
        data = payload.get("data")
        if not isinstance(data, dict):
            return
        key = data.get("key") if isinstance(data.get("key"), dict) else {}
        if key.get("fromMe"):
            return
        remote = str(key.get("remoteJid") or "")
        if remote == self.settings.whatsapp_origin_group_id:
            self._scale(data, moment)
            return
        if self._is_driver_private(remote):
            self._capture_stops(self._text(data), moment)
            return
        if self._command_allowed(remote, str(key.get("participant") or "")):
            self._command(self._text(data), sao_paulo_today(moment))

    def tick(self, now: datetime) -> None:
        local = now.astimezone(SAO_PAULO)
        if local.hour < 8:
            return
        self._close_due(local)
        for key, record in list(self.store.days.items()):
            if record.get("stops") is not None or record.get("stops_asked") or record.get("awaiting_read"):
                continue
            if not record.get("routes"):
                continue
            operation = date.fromisoformat(key)
            if operation != local.date():
                continue
            self._ask_stops(operation, record)

    def _scale(self, data: dict, moment: datetime) -> None:
        text = self._text(data)
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        if "imageMessage" not in message and data.get("messageType") != "imageMessage":
            return
        if "escala" not in text.casefold() and read_operation_date(text, sao_paulo_today(moment)).operation is None:
            if not re.search(r"\d{1,2}/\d{1,2}", text or ""):
                return
        received = sao_paulo_today(moment)
        read = read_operation_date(text, received)
        image = self._image(data)
        reading = self.interpreter.read(text, image, self.settings.driver_name)
        if read.needs_confirmation or not reading.get("confident"):
            self._tell_control(unreadable_scale())
            return
        operation = read.operation
        if operation is None:
            self._tell_control(unreadable_scale())
            return
        record = self.store.ensure_day(operation, self.settings.fuel_default)
        record["routes"] = reading["routes"]
        record["awaiting_read"] = False
        self.store.put_day(operation, record)
        if moment.astimezone(SAO_PAULO).hour >= 8:
            self._ask_stops(operation, record)

    def _close_due(self, local: datetime) -> None:
        if local.hour < 17:
            return
        start, end = period_bounds(local.date())
        if local.date() != end or start.isoformat() in self.store.closed_periods:
            return
        days: list[tuple[date, dict | None]] = []
        gain = Decimal("0")
        fuel = Decimal("0")
        maintenance = Decimal("0")
        has_activity = False
        cursor = start
        while cursor <= end:
            record = self.store.day(cursor)
            if record and record.get("routes") and record.get("stops") is None:
                return
            days.append((cursor, record))
            if record and record.get("routes") and record.get("stops") is not None:
                has_activity = True
                gain += self._day_gain(record)
                fuel += Decimal(record["fuel"])
                maintenance += sum((Decimal(item["amount"]) for item in record["maintenance"]), Decimal("0"))
            cursor = date.fromordinal(cursor.toordinal() + 1)
        if not has_activity and self._pnr_total(start) == 0:
            self.store.mark_closed(start)
            return
        driver_net = self._period_driver_pay(start, end) - self._pnr_total(start)
        driver = self.settings.whatsapp_driver_number.strip()
        if driver:
            self.outbound.send_text(driver, quinzena_driver(start, end, days, self._pnr_total(start)))
        self._tell_control(quinzena_fiorino(start, end, days, driver_net, fuel, maintenance, gain))
        self.store.mark_closed(start)

    def _remember_distance(self, record: dict) -> tuple[Decimal, Decimal] | None:
        stored = self._stored_distance(record)
        if stored is not None:
            return stored
        distance = self.distances.for_routes(record.get("routes") or [])
        if distance is None:
            record["km_ida"] = None
            record["km_volta"] = None
            return None
        record["km_ida"] = str(distance[0])
        record["km_volta"] = str(distance[1])
        return distance

    def _stored_distance(self, record: dict) -> tuple[Decimal, Decimal] | None:
        outbound = record.get("km_ida")
        inbound = record.get("km_volta")
        if not outbound or not inbound:
            return None
        return Decimal(outbound), Decimal(inbound)

    def _day_gain(self, record: dict) -> Decimal:
        routes = record["routes"]
        distance = self._remember_distance(record)
        if distance is None:
            return Decimal("0")
        outbound, inbound = distance
        complete = sum(1 for route in routes if not route["shared"])
        shared = sum(1 for route in routes if route["shared"])
        return (
            freight_for_km(outbound + inbound)
            + stop_bonus(int(record["stops"]))
            + training_bonus(complete + shared, bool(record.get("training", True)))
        )

    def _ask_stops(self, operation: date, record: dict) -> None:
        number = self.settings.whatsapp_driver_number.strip()
        if not number or record.get("stops_asked"):
            return
        message_id = self.outbound.send_text(number, stops_request(record["routes"]))
        if not message_id:
            return
        record["stops_asked"] = True
        self.store.put_day(operation, record)

    def _capture_stops(self, text: str, moment: datetime) -> None:
        pending = [
            (date.fromisoformat(key), record)
            for key, record in self.store.days.items()
            if record.get("stops") is None and record.get("stops_asked") and record.get("routes")
        ]
        if not pending:
            return
        numbers = [int(item) for item in INTEGERS.findall(text or "")]
        if not numbers:
            return
        operation, record = max(pending)
        routes = record["routes"]
        if len(numbers) == 1:
            record["stops"] = numbers[0]
        elif len(numbers) == len(routes):
            record["stops"] = sum(numbers)
        else:
            return
        self.store.put_day(operation, record)
        self._publish(operation, record)

    def _command(self, text: str, today: date) -> None:
        command = parse_command(text, today)
        if command is None or command.needs_confirmation:
            return
        operation = command.operation or today
        if isinstance(command, FuelCommand):
            record = self.store.ensure_day(operation, self.settings.fuel_default)
            record["fuel"] = str(command.amount)
            self.store.put_day(operation, record)
            self._republish(operation, record)
        elif isinstance(command, MaintenanceCommand):
            record = self.store.ensure_day(operation, self.settings.fuel_default)
            record["maintenance"].append(
                {"description": command.description, "amount": str(command.amount)}
            )
            self.store.put_day(operation, record)
            if record.get("routes") and record.get("stops") is not None:
                self._republish(operation, record)
            else:
                self._tell_control(maintenance_only(operation, command.description, command.amount))
        elif isinstance(command, PnrCommand):
            start, end = period_bounds(operation)
            self.store.add_pnr(start, command.amount)
            routes_total = self._period_driver_pay(start, end)
            pnr = self._pnr_total(start)
            if start.isoformat() in self.store.closed_periods:
                days = self._period_days(start, end)
                driver = self.settings.whatsapp_driver_number.strip()
                if driver:
                    self.outbound.send_text(driver, quinzena_driver(start, end, days, pnr))
            self._tell_control(
                "\n".join(
                    [
                        "*Frota Plus*",
                        f"PNR · {start.strftime('%d/%m')} a {end.strftime('%d/%m')}",
                        f"Desconto · {brl(command.amount)}",
                        f"Soma das rotas · {brl(routes_total)}",
                        f"*Total do Douglas · {brl(routes_total - pnr)}*",
                    ]
                )
            )

    def _publish(self, operation: date, record: dict) -> None:
        if record.get("stops") is None or not record.get("routes"):
            return
        text = daily_parecer(
            operation,
            record["routes"],
            int(record["stops"]),
            Decimal(record["fuel"]),
            record["maintenance"],
            bool(record.get("training", True)),
            self._remember_distance(record),
        )
        control = self.settings.whatsapp_control_group_id
        if not control:
            return
        message_id = self.outbound.send_text(control, text)
        if message_id:
            record["control_message_id"] = message_id
            self.store.put_day(operation, record)

    def _republish(self, operation: date, record: dict) -> None:
        control = self.settings.whatsapp_control_group_id
        message_id = record.get("control_message_id")
        if record.get("stops") is None or not record.get("routes") or not control:
            return
        text = daily_parecer(
            operation,
            record["routes"],
            int(record["stops"]),
            Decimal(record["fuel"]),
            record["maintenance"],
            bool(record.get("training", True)),
            self._remember_distance(record),
        )
        if message_id:
            self.outbound.edit_text(control, message_id, text)
        else:
            self._publish(operation, record)

    def _period_days(self, start: date, end: date) -> list[tuple[date, dict | None]]:
        days: list[tuple[date, dict | None]] = []
        cursor = start
        while cursor <= end:
            days.append((cursor, self.store.day(cursor)))
            cursor = date.fromordinal(cursor.toordinal() + 1)
        return days

    def _period_driver_pay(self, start: date, end: date) -> Decimal:
        total = Decimal("0")
        cursor = start
        while cursor <= end:
            record = self.store.day(cursor)
            if record and record.get("routes"):
                complete = sum(1 for route in record["routes"] if not route["shared"])
                shared = sum(1 for route in record["routes"] if route["shared"])
                total += driver_pay(complete, shared)
            cursor = date.fromordinal(cursor.toordinal() + 1)
        return total

    def _pnr_total(self, start: date) -> Decimal:
        return sum(
            (Decimal(item["amount"]) for item in self.store.pnrs if item["period_start"] == start.isoformat()),
            Decimal("0"),
        )

    def _tell_control(self, text: str) -> None:
        control = self.settings.whatsapp_control_group_id
        if control:
            self.outbound.send_text(control, text)

    def _command_allowed(self, remote: str, participant: str) -> bool:
        if not remote or remote == self.settings.whatsapp_origin_group_id:
            return False
        admins = [item.strip() for item in self.settings.whatsapp_admin_numbers.split(",") if item.strip()]
        sender = participant or remote
        if remote == self.settings.whatsapp_control_group_id:
            if not admins:
                return True
            return any(same_phone(sender, admin) for admin in admins)
        if admins and remote.endswith("@s.whatsapp.net"):
            return any(same_phone(remote, admin) for admin in admins)
        return False

    def _is_driver_private(self, remote: str) -> bool:
        return "@g.us" not in remote and same_phone(remote, self.settings.whatsapp_driver_number)

    def _text(self, data: dict) -> str:
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        if message.get("conversation"):
            return str(message["conversation"])
        extended = message.get("extendedTextMessage") or {}
        if isinstance(extended, dict) and extended.get("text"):
            return str(extended["text"])
        image = message.get("imageMessage") or {}
        if isinstance(image, dict) and image.get("caption"):
            return str(image["caption"])
        return ""

    def _image(self, data: dict) -> bytes | None:
        fetcher = getattr(self.outbound, "fetch_image", None)
        key = data.get("key") if isinstance(data.get("key"), dict) else None
        if fetcher is None or key is None:
            return None
        return fetcher(key)


def period_bounds(day: date) -> tuple[date, date]:
    if day.day <= 15:
        return date(day.year, day.month, 1), date(day.year, day.month, 15)
    last = calendar.monthrange(day.year, day.month)[1]
    return date(day.year, day.month, 16), date(day.year, day.month, last)


def _is_upsert(name: str) -> bool:
    compact = name.lower().replace(".", "").replace("_", "")
    return compact in {"messagesupsert", ""}
