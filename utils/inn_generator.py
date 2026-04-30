"""Генератор UZ ИНН.

TODO: точный алгоритм чек-суммы UZ ИНН не подтверждён (см. CLAUDE.md §14 п.4).
Пока генерируем 9 цифр случайно. Если бэкенд отбросит — добавить чек-сумму.
"""

import secrets


def generate_uz_inn() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(9))
