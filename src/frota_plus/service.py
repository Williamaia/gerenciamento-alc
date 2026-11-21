"""Orquestra o dia: escala, paradas, comandos e parecer."""

import calendar
import logging
import re
from datetime import date, datetime
from decimal import Decimal

from frota_plus.commands import (
    FuelCommand,
    HelpCommand,
    MaintenanceCommand,
    PnrCommand,
    RetryCommand,
    parse_command,
)
from frota_plus.config import Settings
from frota_plus.domain.dates import DATE_PATTERN, SAO_PAULO, read_operation_date, sao_paulo_today
from frota_plus.domain.money import brl, driver_pay
from frota_plus.outbound import Outbound
from frota_plus.phones import same_phone
from frota_plus.domain.money import freight_for_km, stop_bonus, training_bonus
from frota_plus.routing import DistanceBook, fetch_road_leg
from frota_plus.reports import (
    audit_date_problem,
    audit_done,
    audit_download_failed,
    audit_photo_read,
    audit_processing_failed,
    audit_reader_failed,
    audit_retry_unconfident,
    audit_send_failed,
    audit_stops_locked,
    audit_unconfident,
    daily_parecer,
    help_text,
    maintenance_only,
    quinzena_driver,
    quinzena_fiorino,
    retry_confirmed,
    retry_nothing,
    retry_stops_locked,
    stops_reminder,
    stops_request,
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
        remote = str(key.get("remoteJid") or "")
        text = self._text(data)
        logger.info("evento_recebido from_me=%s grupo=%s", bool(key.get("fromMe")), remote.endswith("@g.us"))
        today = sao_paulo_today(moment)
        if key.get("fromMe"):
            if remote == self.settings.whatsapp_control_group_id and parse_command(text, today) is not None:
                self._command(text, today, remote, moment)
            return
        if remote == self.settings.whatsapp_origin_group_id:
            self._scale(data, moment)
            return
        if remote == self.settings.whatsapp_audit_group_id:
            return
        if self._is_driver_private(remote):
            self._capture_stops(text, moment)
            return
        if self._command_allowed(remote, str(key.get("participant") or "")):
            self._command(text, today, remote, moment)

    def tick(self, now: datetime) -> None:
        logger.info("agenda_ciclo")
        local = now.astimezone(SAO_PAULO)
        if local.hour < 8:
            logger.info("agenda_sem_efeito")
            return
        closed = self._close_due(local)
        acted = closed
        for key, record in list(self.store.days.items()):
            if record.get("stops") is not None or record.get("awaiting_read"):
                continue
            if not record.get("routes"):
                continue
            operation = date.fromisoformat(key)
            if operation != local.date():
                continue
            if not record.get("stops_asked"):
                acted = self._ask_stops(operation, record) or acted
                continue
            if local.hour >= 10 and not record.get("stops_reminded"):
                acted = self._remind_stops(operation, record) or acted
        if not acted:
            logger.info("agenda_sem_efeito")

    def _scale(self, data: dict, moment: datetime) -> None:
        text = self._text(data)
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        if "imageMessage" not in message and data.get("messageType") != "imageMessage":
            return
        if "escala" not in text.casefold() and read_operation_date(text, sao_paulo_today(moment)).operation is None:
            if not re.search(r"\d{1,2}/\d{1,2}", text or ""):
                return
        self._ingest_scale(data, moment, from_retry=False)

    def register_manual_scale(self, payload: dict, now: datetime) -> tuple[int, dict]:
        received = sao_paulo_today(now)
        operation, routes = _manual_scale(payload, received)
        if operation is None or routes is None:
            return 400, {"error": "invalid_body"}
        current = self.store.day(operation)
        if current is not None and current.get("stops") is not None:
            return 409, {"error": "stops_already_recorded"}
        record = self.store.ensure_day(operation, self.settings.fuel_default)
        previous = list(record.get("routes") or [])
        if _route_codes(previous) != _route_codes(routes):
            record["stops_asked"] = False
            record["stops_reminded"] = False
        if previous != routes:
            record["km_ida"] = None
            record["km_volta"] = None
            record.pop("km_method", None)
        record["routes"] = routes
        record["stops"] = None
        record["awaiting_read"] = False
        self.store.put_day(operation, record)
        local = now.astimezone(SAO_PAULO)
        sent = False
        if operation == local.date() and local.hour >= 8 and not record.get("stops_asked"):
            self._ask_stops(operation, record)
            sent = bool(record.get("stops_asked"))
        logger.info("escala_manual data=%s rotas=%s pedido=%s", operation.isoformat(), len(routes), sent)
        return 200, {"accepted": True, "pedidoEnviado": sent}

    def _close_due(self, local: datetime) -> bool:
        if local.hour < 17:
            return False
        start, end = period_bounds(local.date())
        if local.date() != end or start.isoformat() in self.store.closed_periods:
            return False
        days: list[tuple[date, dict | None]] = []
        gain = Decimal("0")
        fuel = Decimal("0")
        maintenance = Decimal("0")
        has_activity = False
        cursor = start
        while cursor <= end:
            record = self.store.day(cursor)
            if record and record.get("routes") and record.get("stops") is None:
                return False
            days.append((cursor, record))
            if record and record.get("routes") and record.get("stops") is not None:
                has_activity = True
                gain += self._day_gain(record)
                fuel += Decimal(record["fuel"])
                maintenance += sum((Decimal(item["amount"]) for item in record["maintenance"]), Decimal("0"))
            cursor = date.fromordinal(cursor.toordinal() + 1)
        if not has_activity and self._pnr_total(start) == 0:
            self.store.mark_closed(start)
            return True
        driver_net = self._period_driver_pay(start, end) - self._pnr_total(start)
        driver = self.settings.whatsapp_driver_number.strip()
        if driver:
            self.outbound.send_text(driver, quinzena_driver(start, end, days, self._pnr_total(start)))
        self._tell_control(quinzena_fiorino(start, end, days, driver_net, fuel, maintenance, gain))
        self._note_success("Fechamento da quinzena enviado.")
        self.store.mark_closed(start)
        return True

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
        record["km_method"] = "chain"
        return distance

    def _stored_distance(self, record: dict) -> tuple[Decimal, Decimal] | None:
        if record.get("km_method") == "pending-chain":
            return None
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

    def _ask_stops(self, operation: date, record: dict) -> bool:
        number = self.settings.whatsapp_driver_number.strip()
        if not number or record.get("stops_asked"):
            return False
        message_id = self.outbound.send_text(number, stops_request(record["routes"]))
        if not message_id:
            return False
        record["stops_asked"] = True
        self.store.put_day(operation, record)
        self._note_success("Pedido de paradas enviado.")
        return True

    def _remind_stops(self, operation: date, record: dict) -> bool:
        number = self.settings.whatsapp_driver_number.strip()
        if not number or record.get("stops_reminded"):
            return False
        message_id = self.outbound.send_text(number, stops_reminder(record["routes"]))
        if not message_id:
            return False
        record["stops_reminded"] = True
        self.store.put_day(operation, record)
        self._note_success("Lembrete de paradas enviado.")
        return True

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
        self._note_success("Paradas gravadas.")

    def _command(self, text: str, today: date, remote: str, moment: datetime) -> None:
        command = parse_command(text, today)
        if command is None:
            return
        logger.info("comando %s", type(command).__name__)
        if isinstance(command, HelpCommand):
            if remote and remote != self.settings.whatsapp_origin_group_id:
                self.outbound.send_text(remote, help_text())
            self._note_success("Ajuda enviada.")
            return
        if isinstance(command, RetryCommand):
            self._retry(moment)
            return
        if command.needs_confirmation:
            return
        operation = command.operation or today
        if isinstance(command, FuelCommand):
            record = self.store.ensure_day(operation, self.settings.fuel_default)
            record["fuel"] = str(command.amount)
            self.store.put_day(operation, record)
            self._republish(operation, record)
            self._note_success("Combustível ajustado.")
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
            self._note_success("Manutenção registrada.")
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
            self._note_success("PNR registrado.")

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
        self._note_success(f"Parecer de {operation.strftime('%d/%m/%Y')} enviado.")
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
            self.store.put_day(operation, record)
        else:
            self._publish(operation, record)

    def refresh_pending_routes(self) -> None:
        for key, record in list(self.store.days.items()):
            if record.get("km_method") != "pending-chain":
                continue
            if record.get("stops") is None or not record.get("routes"):
                continue
            self._republish(date.fromisoformat(key), record)

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

    def _retry(self, moment: datetime) -> None:
        pending = self.store.pending_scale
        if not isinstance(pending, dict) or not pending.get("key"):
            self._tell_control(retry_nothing())
            return
        data = {
            "key": pending["key"],
            "message": {"imageMessage": {"caption": str(pending.get("text") or "")}},
            "messageType": "imageMessage",
        }
        self._ingest_scale(data, moment, from_retry=True)

    def _ingest_scale(self, data: dict, moment: datetime, from_retry: bool) -> None:
        text = self._text(data)
        received = sao_paulo_today(moment)
        logger.info("leitura_inicio retry=%s", from_retry)
        problem = _date_problem(text, received)
        if problem is not None:
            self._keep_pending(data, text)
            self._tell_audit(audit_date_problem(problem))
            return
        operation = read_operation_date(text, received).operation
        if operation is None:
            self._keep_pending(data, text)
            self._tell_audit(audit_date_problem("O texto da mensagem não tem data utilizável."))
            return
        current = self.store.day(operation)
        if current is not None and current.get("stops") is not None:
            if from_retry:
                self._tell_control(retry_stops_locked())
            self._tell_audit(audit_stops_locked())
            return
        image = self._image(data)
        if not image:
            logger.info("leitura_sem_arquivo")
            self._keep_pending(data, text)
            self._tell_audit(audit_download_failed())
            return
        reading = self.interpreter.read(text, image, self.settings.driver_name)
        status = str(reading.get("status") or ("ok" if reading.get("confident") else "unconfident"))
        if status == "error":
            self._keep_pending(data, text)
            self._tell_audit(audit_reader_failed())
            return
        if not reading.get("confident"):
            self._keep_pending(data, text)
            self._tell_audit(audit_retry_unconfident() if from_retry else audit_unconfident())
            return
        routes = list(reading.get("routes") or [])
        record = self.store.ensure_day(operation, self.settings.fuel_default)
        record["routes"] = routes
        record["awaiting_read"] = False
        self.store.put_day(operation, record)
        self.store.set_pending_scale(None)
        codes = [str(route.get("code") or "") for route in routes if route.get("code")]
        self._tell_audit(audit_photo_read(operation, codes))
        if from_retry:
            self._tell_control(retry_confirmed(operation, codes))
        logger.info("leitura_gravada data=%s rotas=%s", operation.isoformat(), len(codes))
        if moment.astimezone(SAO_PAULO).hour >= 8:
            self._ask_stops(operation, record)

    def _keep_pending(self, data: dict, text: str) -> None:
        key = data.get("key") if isinstance(data.get("key"), dict) else {}
        kept = {}
        for name in ("id", "remoteJid", "fromMe", "participant", "remoteJidAlt", "participantAlt"):
            if name in key:
                kept[name] = key[name]
        self.store.set_pending_scale({"key": kept, "text": text})

    def _note_success(self, line: str) -> None:
        self._tell_audit(audit_done(line))

    def _tell_audit(self, text: str) -> None:
        audit = self.settings.whatsapp_audit_group_id.strip()
        logger.info("auditoria destino=%s", "configurado" if audit else "ausente")
        if audit:
            self.outbound.send_text(audit, text)

    def report_send_failure(self, status: int, path: str) -> None:
        logger.info("envio_falhou status=%s path=%s", status, path)
        self._tell_audit(audit_send_failed())

    def report_processing_failure(self) -> None:
        logger.info("processamento_falhou")
        self._tell_audit(audit_processing_failed())

    def _tell_control(self, text: str) -> None:
        control = self.settings.whatsapp_control_group_id
        if control:
            self.outbound.send_text(control, text)

    def _command_allowed(self, remote: str, participant: str) -> bool:
        if not remote or remote == self.settings.whatsapp_origin_group_id:
            return False
        if remote == self.settings.whatsapp_audit_group_id:
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


def _date_problem(text: str, received: date) -> str | None:
    found = DATE_PATTERN.findall(text or "")
    if len(found) == 0:
        return "O texto da mensagem não tem data utilizável."
    if len(found) > 1:
        return "O texto da mensagem tem mais de uma data."
    read = read_operation_date(text, received)
    if read.needs_confirmation:
        return "A data pede confirmação."
    if read.operation is None:
        return "O texto da mensagem não tem data utilizável."
    return None


def period_bounds(day: date) -> tuple[date, date]:
    if day.day <= 15:
        return date(day.year, day.month, 1), date(day.year, day.month, 15)
    last = calendar.monthrange(day.year, day.month)[1]
    return date(day.year, day.month, 16), date(day.year, day.month, last)


def _is_upsert(name: str) -> bool:
    compact = name.lower().replace(".", "").replace("_", "")
    return compact in {"messagesupsert", ""}


def _route_codes(routes: list[dict]) -> list[str]:
    return [str(route.get("code") or "") for route in routes]


def _manual_scale(payload: dict, received: date) -> tuple[date | None, list[dict] | None]:
    raw_date = payload.get("data")
    if not isinstance(raw_date, str) or not raw_date.strip():
        return None, None
    read = read_operation_date(raw_date.strip(), received)
    if read.operation is None or read.needs_confirmation:
        return None, None
    raw_routes = payload.get("rotas")
    if not isinstance(raw_routes, list) or not raw_routes:
        return None, None
    routes: list[dict] = []
    for item in raw_routes:
        if not isinstance(item, dict):
            return None, None
        code = item.get("codigo")
        cities = item.get("cidades")
        if not isinstance(code, str) or not code.strip():
            return None, None
        if not isinstance(cities, list) or not cities:
            return None, None
        if any(not isinstance(city, str) or not city.strip() for city in cities):
            return None, None
        if "compartilhada" in item and not isinstance(item["compartilhada"], bool):
            return None, None
        routes.append(
            {
                "code": code.strip(),
                "cities": [city.strip() for city in cities],
                "shared": bool(item.get("compartilhada", False)),
            }
        )
    return read.operation, routes
