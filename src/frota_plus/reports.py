"""Textos enviados ao grupo de controle e ao Douglas."""

from datetime import date
from decimal import Decimal

from frota_plus.domain.money import brl, day_profit, driver_pay, freight_for_km, stop_bonus, training_bonus


def format_day(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def short_day(value: date) -> str:
    return value.strftime("%d/%m")


def daily_parecer(
    operation: date,
    routes: list[dict],
    stops: int,
    fuel: Decimal,
    maintenance: list[dict],
    training: bool,
    distance: tuple[Decimal, Decimal] | None = None,
) -> str:
    complete = sum(1 for route in routes if not route["shared"])
    shared = sum(1 for route in routes if route["shared"])
    pay = driver_pay(complete, shared)
    cities = [city for route in routes for city in route["cities"]]
    codes = ", ".join(route["code"] for route in routes) or "pendente"
    city_text = ", ".join(cities) or "pendente"
    maintenance_total = sum((Decimal(item["amount"]) for item in maintenance), Decimal("0"))
    lines = [
        "*Frota Plus*",
        f"_{format_day(operation)}_",
        "",
        f"*Douglas · {codes}*",
        city_text,
    ]
    if distance is None:
        lines.append("Quilometragem · pendente")
        gain = None
    else:
        outbound, inbound = distance
        total_km = outbound + inbound
        fare = freight_for_km(total_km)
        bonus = stop_bonus(stops)
        training_amount = training_bonus(complete + shared, training)
        gain = fare + bonus + training_amount
        lines.extend(
            [
                f"{total_km} km · {outbound} de ida e {inbound} de volta",
                f"{stops} paradas",
                "",
                "*Fiorino*",
                f"Frete · {brl(fare)}",
                f"Paradas · {brl(bonus)}",
                f"Treinamento · {brl(training_amount)}",
                f"*Ganho · {brl(gain)}*",
            ]
        )
    lines.extend(["", "*Resultado do dia*", f"Motorista · {brl(pay)}", f"Combustível · {brl(fuel)}"])
    for item in maintenance:
        lines.append(f"{item['description']} · {brl(Decimal(item['amount']))}")
    if gain is None:
        lines.append("*Lucro · pendente*")
    else:
        lines.append(f"*Lucro · {brl(day_profit(gain, pay, fuel, maintenance_total))}*")
    return "\n".join(lines)


def _route_codes(routes: list[dict]) -> str:
    return "\n".join(route["code"] for route in routes)


def stops_request(routes: list[dict]) -> str:
    return "\n".join(
        [
            "Olá. Sou o agente da Frota Plus.",
            "Por favor, informe a quantidade de paradas das seguintes rotas:",
            _route_codes(routes),
            "",
            "Informe somente a quantidade de paradas. Não é necessário informar a quantidade de pacotes.",
        ]
    )


def stops_reminder(routes: list[dict]) -> str:
    return "\n".join(
        [
            "Olá. Sou o agente da Frota Plus.",
            "Ainda não recebi a quantidade de paradas das seguintes rotas:",
            _route_codes(routes),
            "",
            "Informe somente a quantidade de paradas. Não é necessário informar a quantidade de pacotes.",
        ]
    )


def maintenance_only(operation: date, description: str, amount: Decimal) -> str:
    return "\n".join(
        [
            "*Frota Plus*",
            f"Manutenção {format_day(operation)}",
            f"{description} · {brl(amount)}",
        ]
    )


def quinzena_driver(start: date, end: date, days: list[tuple[date, dict | None]], pnr: Decimal) -> str:
    lines = [
        "*Frota Plus*",
        "Demonstrativo de pagamento",
        "Douglas",
        f"{format_day(start)} a {format_day(end)}",
        "",
    ]
    complete = 0
    shared = 0
    worked = 0
    total = Decimal("0")
    for operation, record in days:
        routes = (record or {}).get("routes") or []
        if not routes:
            lines.append(f"{short_day(operation)} · sem rota · R$ 0,00")
            continue
        worked += 1
        for route in routes:
            amount = Decimal("50.00") if route["shared"] else Decimal("100.00")
            kind = "compartilhada" if route["shared"] else "completa"
            if route["shared"]:
                shared += 1
            else:
                complete += 1
            total += amount
            lines.append(f"{short_day(operation)} · {route['code']} · {kind} · {brl(amount)}")
    lines.extend(
        [
            "",
            f"Rotas completas · {complete}",
            f"Rotas compartilhadas · {shared}",
            f"Dias trabalhados · {worked}",
            f"Soma das rotas · {brl(total)}",
            f"PNR · {brl(pnr)}",
            f"*Total a receber · {brl(total - pnr)}*",
        ]
    )
    return "\n".join(lines)


def quinzena_fiorino(
    start: date,
    end: date,
    days: list[tuple[date, dict | None]],
    driver_net: Decimal,
    fuel: Decimal,
    maintenance: Decimal,
    gain: Decimal,
) -> str:
    lines = [
        "*Frota Plus*",
        "Relatório da Fiorino",
        f"{format_day(start)} a {format_day(end)}",
        "",
    ]
    for operation, record in days:
        routes = (record or {}).get("routes") or []
        if not routes or record is None or record.get("stops") is None:
            lines.append(f"{short_day(operation)} · sem rota · R$ 0,00")
            continue
        lines.append(f"{short_day(operation)} · {', '.join(route['code'] for route in routes)}")
    lines.extend(
        [
            "",
            f"*Ganhos da quinzena · {brl(gain)}*",
            "",
            f"Pagamentos do Douglas · {brl(driver_net)}",
            f"Abastecimentos · {brl(fuel)}",
            f"Manutenções · {brl(maintenance)}",
            f"*Lucro da quinzena · {brl(gain - driver_net - fuel - maintenance)}*",
        ]
    )
    return "\n".join(lines)


def unreadable_scale() -> str:
    return "\n".join(
        [
            "*Frota Plus*",
            "Não consegui ler a escala com segurança.",
            "Preciso que você leia a imagem e confirme.",
        ]
    )
