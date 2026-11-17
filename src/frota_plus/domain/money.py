"""Cálculos financeiros. O modelo não inventa estes valores."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
COMPLETE_ROUTE = Decimal("100.00")
SHARED_ROUTE = Decimal("50.00")
TRAINING_PER_ROUTE = Decimal("5.00")

FREIGHT_BANDS = (
    (Decimal("100"), Decimal("235.00")),
    (Decimal("150"), Decimal("260.00")),
    (Decimal("200"), Decimal("305.00")),
    (Decimal("250"), Decimal("335.00")),
    (Decimal("300"), Decimal("355.00")),
)


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def brl(value: Decimal) -> str:
    quantized = money(value)
    sign = "-" if quantized < 0 else ""
    rendered = f"{abs(quantized):.2f}".replace(".", ",")
    return f"{sign}R$ {rendered}"


def parse_amount(text: str) -> Decimal:
    cleaned = text.strip().replace("R$", "").replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    amount = Decimal(cleaned)
    if amount < 0:
        raise ValueError("valor negativo")
    return money(amount)


def driver_pay(complete: int, shared: int) -> Decimal:
    if complete < 0 or shared < 0:
        raise ValueError("quantidade negativa")
    return money(COMPLETE_ROUTE * complete + SHARED_ROUTE * shared)


def stop_bonus(stops: int) -> Decimal:
    if stops < 0:
        raise ValueError("paradas negativas")
    total = Decimal("0")
    for index in range(1, stops + 1):
        if index <= 60:
            total += Decimal("0.35")
        elif index <= 90:
            total += Decimal("1.90")
        else:
            total += Decimal("0.90")
    return money(total)


def freight_for_km(kilometers: Decimal) -> Decimal:
    if kilometers < 0:
        raise ValueError("quilometragem negativa")
    for limit, amount in FREIGHT_BANDS:
        if kilometers <= limit:
            return amount
    return Decimal("380.00")


def training_bonus(routes: int, enabled: bool) -> Decimal:
    if routes < 0:
        raise ValueError("rotas negativas")
    if not enabled or routes == 0:
        return Decimal("0.00")
    return money(TRAINING_PER_ROUTE * routes)


def day_profit(
    fiorino_gain: Decimal,
    driver: Decimal,
    fuel: Decimal,
    maintenance: Decimal,
) -> Decimal:
    return money(fiorino_gain - driver - fuel - maintenance)
