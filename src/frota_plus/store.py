"""Memória operacional em arquivo. O cálculo continua no backend."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from threading import Lock


class Store:
    def __init__(self, path: Path | None) -> None:
        self.path = path
        self._lock = Lock()
        self.days: dict[str, dict] = {}
        self.pnrs: list[dict] = []
        self.closed_periods: list[str] = []
        self.distances: dict[str, dict] = {}
        if path and path.exists():
            self._load(path)

    def _load(self, path: Path) -> None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.days = raw.get("days", {})
        self.pnrs = raw.get("pnrs", [])
        self.closed_periods = raw.get("closed_periods", [])
        self.distances = raw.get("distances", {})

    def save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "days": self.days,
            "pnrs": self.pnrs,
            "closed_periods": self.closed_periods,
            "distances": self.distances,
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def day(self, operation: date) -> dict | None:
        return self.days.get(operation.isoformat())

    def ensure_day(self, operation: date, fuel: Decimal) -> dict:
        key = operation.isoformat()
        with self._lock:
            current = self.days.get(key)
            if current is None:
                current = {
                    "routes": [],
                    "stops": None,
                    "stops_asked": False,
                    "fuel": str(fuel),
                    "maintenance": [],
                    "training": True,
                    "control_message_id": None,
                    "awaiting_read": False,
                }
                self.days[key] = current
            return current

    def put_day(self, operation: date, record: dict) -> None:
        with self._lock:
            self.days[operation.isoformat()] = record
            self.save()

    def mark_closed(self, period_start: date) -> None:
        with self._lock:
            key = period_start.isoformat()
            if key not in self.closed_periods:
                self.closed_periods.append(key)
            self.save()

    def add_pnr(self, period_start: date, amount: Decimal) -> None:
        with self._lock:
            self.pnrs.append({"period_start": period_start.isoformat(), "amount": str(amount)})
            self.save()
