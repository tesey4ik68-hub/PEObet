"""
Модуль для определения путей в проекте.
"""

from pathlib import Path

# Корневая директория проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Директории
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
DATA_DIR = PROJECT_ROOT / "data"  # Исправлено: база данных в корне проекта
DOCUMENTS_DIR = PROJECT_ROOT / "Документы"  # Исправлено: документы в корне проекта
PASSPORTS_DIR = DOCUMENTS_DIR / "Паспорта"
PROTOCOLS_DIR = DOCUMENTS_DIR / "Протоколы"
COMPACT_DIR = DOCUMENTS_DIR / "Заключения"
JOURNALS_DIR = DOCUMENTS_DIR / "Журналы"
