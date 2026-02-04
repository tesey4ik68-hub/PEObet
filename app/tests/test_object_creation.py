"""
Тесты для проверки создания и работы с объектами.
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseManager
from gui.start_dialog import StartDialog
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt


def test_create_and_use_object():
    """Тест создания объекта и его использования."""
    print("=== Тест создания и использования объекта ===")
    
    # Создаем временную базу данных для теста
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = Path(temp_dir) / "test_app.db"
        db = DatabaseManager(db_path)
        
        # Проверяем, что таблица objects создана с нужными колонками
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(objects)")
                columns = cursor.fetchall()
                print(f"Колонки в таблице objects: {[col[1] for col in columns]}")
                
                # Проверяем наличие нужных колонок
                column_names = [col[1] for col in columns]
                if 'firm' in column_names:
                    print("✓ Колонка 'firm' существует в таблице objects")
                else:
                    print("✗ Колонка 'firm' отсутствует в таблице objects")
                    return False
                    
        except Exception as e:
            print(f"Ошибка проверки таблицы objects: {e}")
            return False
        
        # Создаем тестовый объект через SQL напрямую
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO objects (name, address, firm)
                    VALUES (?, ?, ?)
                """, ("Руднево 8", "Некрасовка", "ООО ТЕСТ"))
                conn.commit()
                print("✓ Объект успешно создан в базе данных")
        except Exception as e:
            print(f"Ошибка создания объекта в базе: {e}")
            return False
        
        # Проверяем, что объект сохранился
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, address, firm FROM objects WHERE name = ?", ("Руднево 8",))
                row = cursor.fetchone()
                if row:
                    print(f"✓ Объект найден в БД: {row}")
                    if row[2] == "ООО ТЕСТ":
                        print("✓ Данные объекта корректны")
                    else:
                        print("✗ Данные объекта некорректны")
                        return False
                else:
                    print("✗ Объект не найден в БД")
                    return False
        except Exception as e:
            print(f"Ошибка проверки объекта в БД: {e}")
            return False
    finally:
        # Явно закрываем соединение с БД
        try:
            db.close()
        except Exception as e:
            print(f"Ошибка закрытия БД: {e}")
        # Принудительно очищаем память
        import gc
        gc.collect()
        # Удаляем временную директорию
        import shutil
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Ошибка удаления временной директории: {e}")
            
    return True


def main():
    """Основная функция тестирования."""
    print("Запуск тестов создания и работы с объектами...")
    
    success = test_create_and_use_object()
    
    if success:
        print("✓ Все тесты прошли успешно!")
        return 0
    else:
        print("✗ Тесты не пройдены")
        return 1


if __name__ == "__main__":
    exit(main())