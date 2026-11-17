"""Comparação de telefones brasileiros, com ou sem o nono dígito."""


def digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def canonical_br(value: str) -> str:
    number = digits(value)
    if number.startswith("55"):
        number = number[2:]
    if len(number) == 11 and number[2] == "9":
        number = number[:2] + number[3:]
    return number


def same_phone(left: str, right: str) -> bool:
    if not digits(left) or not digits(right):
        return False
    return canonical_br(left) == canonical_br(right)
