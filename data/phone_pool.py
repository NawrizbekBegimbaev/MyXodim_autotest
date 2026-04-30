"""Атомарная выдача тестовых телефонов из пула с filelock (для xdist).

Состояние хранится в JSON. Каждый воркер берёт первый свободный номер,
помечает занятым, в teardown возвращает обратно.

Также: `random_test_phone()` для одноразовых телефонов в creating-тестах
(после успешного create телефон занят в БД и не подлежит переиспользованию).
"""

import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock

_STATE_DIR = Path(".phone_pool")
_STATE_FILE = _STATE_DIR / "state.json"
_LOCK_FILE = _STATE_DIR / "state.lock"


def _format_phone(index: int) -> str:
    return f"+99890{index:07d}"


def _ensure_state(start: int, size: int) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    if _STATE_FILE.exists():
        return
    pool = {_format_phone(i): "free" for i in range(start, start + size)}
    _STATE_FILE.write_text(json.dumps(pool, indent=2), encoding="utf-8")


def _load() -> dict[str, str]:
    data: dict[str, str] = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    return data


def _save(state: dict[str, str]) -> None:
    _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def acquire(start: int, size: int) -> str:
    _ensure_state(start, size)
    with FileLock(str(_LOCK_FILE)):
        state = _load()
        for phone, status in state.items():
            if status == "free":
                state[phone] = "busy"
                _save(state)
                return phone
        raise RuntimeError(f"Phone pool exhausted (size={size}). Increase PHONE_POOL_SIZE.")


def release(phone: str) -> None:
    with FileLock(str(_LOCK_FILE)):
        state = _load()
        if phone in state:
            state[phone] = "free"
            _save(state)


@contextmanager
def lease(start: int, size: int) -> Iterator[str]:
    phone = acquire(start, size)
    try:
        yield phone
    finally:
        release(phone)


def random_test_phone() -> str:
    """Рандомный +998 90 XXXXXXX. Для creating-тестов где телефон одноразовый.

    10M вариантов — коллизии пренебрежимо редки. Если коллизия случится,
    бэк отбросит создание, тест корректно упадёт с понятной ошибкой UI.
    """
    return f"+99890{secrets.randbelow(10_000_000):07d}"
