"""
Модуль нумерации для генерации номеров документов.
"""

from datetime import datetime, timedelta, date
from typing import Optional


def normalize_date(d) -> date:
    """Нормализует дату: QDate, datetime или date -> date."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    # Если QDate (PySide6)
    if hasattr(d, 'toPython'):
        return d.toPython()
    raise ValueError(f"Неподдерживаемый тип даты: {type(d)}")


def excel_serial_date(date_input) -> int:
    """Преобразует дату в Excel серийный номер."""
    d = normalize_date(date_input)
    base = date(1899, 12, 30)
    return (d - base).days + 1


def generate_passport_number(pour_date, existing_numbers: list[str]) -> str:
    """Генерирует номер паспорта: 17-0000 + Excel серийный номер даты + счетчик при дубликате."""
    serial = excel_serial_date(pour_date)
    base = f"17-0000{serial:05d}"
    
    # Подсчитываем количество существующих номеров с тем же основанием
    count = sum(1 for num in existing_numbers if num.startswith(base))
    
    # Если таких нет, возвращаем базовый номер
    if count == 0:
        return base
    
    # Иначе добавляем суффикс -2, -3 и т.д.
    return f"{base}-{count + 1}"


def generate_protocol_number(pour_date, age_days: int, existing_numbers: list[str]) -> str:
    """Генерирует номер протокола: ДД.ММ.N-возраст/ГГ"""
    test_date = normalize_date(pour_date) + timedelta(days=age_days)
    day = test_date.day
    month = test_date.month
    year_short = test_date.year % 100
    base = f"{day:02d}.{month:02d}."
    counter = 1
    candidate = f"{base}{counter}-{age_days}/{year_short:02d}"
    while candidate in existing_numbers:
        counter += 1
        candidate = f"{base}{counter}-{age_days}/{year_short:02d}"
    return candidate


def generate_conclusion_number(end_date, existing_numbers: list[str]) -> str:
    """Генерирует номер заключения: ДД.ММ.N/ГГ"""
    d = normalize_date(end_date)
    day = d.day
    month = d.month
    year_short = d.year % 100
    base = f"{day:02d}.{month:02d}."
    counter = 1
    candidate = f"{base}{counter}/{year_short:02d}"
    while candidate in existing_numbers:
        counter += 1
        candidate = f"{base}{counter}/{year_short:02d}"
    return candidate
