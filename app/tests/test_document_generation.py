"""
Тесты для проверки генерации документов.
"""

import os
import sys
import tempfile
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import DatabaseManager
from core.services.document_service import DocumentService, DocumentType, LabType
from core.paths import DATA_DIR, TEMPLATES_DIR, PASSPORTS_DIR, PROTOCOLS_DIR


def test_passport_generation():
    """Тест генерации паспорта."""
    print("=== Тест генерации паспорта ===")
    
    # Создаем временную базу данных для теста
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = Path(temp_dir) / "test_app.db"
        db = DatabaseManager(db_path)
        
        # Создаем сервис
        service = DocumentService(db)
        
        # Подготовка тестовых данных
        entry = {
            "grade": "В25",
            "volume": 10,
            "pour_date": "2026-01-29",
            "network": "Секция 1",
            "area": "Участок А",
            "object_name": "Тестовый объект",
            "address": "г. Москва, ул. Тестовая 1",
            "firm": "ООО Бетон"
        }
        
        try:
            # Генерируем паспорт
            result = service.generate_documents([entry], DocumentType.PASSPORT)
            print(f"✓ Паспорт сгенерирован успешно: {result}")
            
            # Проверяем, что файл был создан
            if result and len(result) > 0:
                file_path = result[0]
                if file_path.exists():
                    print(f"✓ Файл паспорта создан: {file_path}")
                else:
                    print(f"✗ Файл паспорта не создан: {file_path}")
                    return False
            else:
                print("✗ Не удалось получить путь к сгенерированному файлу")
                return False
                
            # Проверяем, что запись сохранена в базе
            passports = db.get_passports()
            if passports:
                print(f"✓ Запись паспорта сохранена в БД: {passports[0]}")
            else:
                print("✗ Запись паспорта не сохранена в БД")
                return False
                
            return True
            
        except Exception as e:
            print(f"✗ Ошибка при генерации паспорта: {e}")
            import traceback
            traceback.print_exc()
            return False
    finally:
        # Очищаем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_protocol_generation():
    """Тест генерации протокола."""
    print("\n=== Тест генерации протокола ===")
    
    # Создаем временную базу данных для теста
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = Path(temp_dir) / "test_app.db"
        db = DatabaseManager(db_path)
        
        # Создаем сервис
        service = DocumentService(db)
        
        # Подготовка тестовых данных
        entry = {
            "grade": "В25",
            "volume": 10,
            "pour_date": "2026-01-29",
            "network": "Секция 1",
            "area": "Участок А",
            "object_name": "Тестовый объект",
            "address": "г. Москва, ул. Тестовая 1",
            "firm": "ООО Бетон"
        }
        
        try:
            # Генерируем протокол 7 дней
            result = service.generate_documents([entry], DocumentType.PROTOCOL_7, LabType.LIK)
            print(f"✓ Протокол 7 дней сгенерирован успешно: {result}")
            
            # Проверяем, что файл был создан
            if result and len(result) > 0:
                file_path = result[0]
                if file_path.exists():
                    print(f"✓ Файл протокола создан: {file_path}")
                else:
                    print(f"✗ Файл протокола не создан: {file_path}")
                    return False
            else:
                print("✗ Не удалось получить путь к сгенерированному файлу")
                return False
                
            # Проверяем, что запись сохранена в базе
            protocols = db.get_protocols()
            if protocols:
                print(f"✓ Запись протокола сохранена в БД: {protocols[0]}")
            else:
                print("✗ Запись протокола не сохранена в БД")
                return False
                
            return True
            
        except Exception as e:
            print(f"✗ Ошибка при генерации протокола: {e}")
            import traceback
            traceback.print_exc()
            return False
    finally:
        # Очищаем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_combo_generation():
    """Тест генерации COMBO."""
    print("\n=== Тест генерации COMBO ===")
    
    # Создаем временную базу данных для теста
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = Path(temp_dir) / "test_app.db"
        db = DatabaseManager(db_path)
        
        # Создаем сервис
        service = DocumentService(db)
        
        # Подготовка тестовых данных
        entry = {
            "grade": "В25",
            "volume": 10,
            "pour_date": "2026-01-29",
            "network": "Секция 1",
            "area": "Участок А",
            "object_name": "Тестовый объект",
            "address": "г. Москва, ул. Тестовая 1",
            "firm": "ООО Бетон"
        }
        
        try:
            # Генерируем COMBO
            result = service.generate_documents([entry], DocumentType.COMBO, LabType.PTS)
            print(f"✓ COMBO сгенерирован успешно: {len(result)} файлов")
            
            # Проверяем, что файлы были созданы
            if result and len(result) >= 3:  # паспорт + 2 протокола
                passport_created = False
                protocol_7_created = False
                protocol_28_created = False
                
                # Выводим информацию о файлах для отладки
                print(f"DEBUG: Проверяем {len(result)} файлов:")
                for i, file_path in enumerate(result):
                    print(f"DEBUG: Файл {i+1}: {file_path}")
                    print(f"DEBUG: Файл существует: {file_path.exists()}")
                    print(f"DEBUG: Имя файла: {file_path.name}")
                    
                for file_path in result:
                    if file_path.exists():
                        print(f"✓ Файл создан: {file_path}")
                        # Исправлено: проверка на содержание в имени файла
                        if "паспорт" in file_path.name:
                            passport_created = True
                        elif "протокол" in file_path.name:
                            # Проверяем, какой протокол это: 7 или 28
                            # Выводим отладочную информацию
                            print(f"DEBUG: Проверка протокола: {file_path.name}")
                            if "7" in file_path.name:
                                print("DEBUG: Найден протокол 7 дней")
                                protocol_7_created = True
                            elif "28" in file_path.name:
                                print("DEBUG: Найден протокол 28 дней")
                                protocol_28_created = True
                    else:
                        print(f"✗ Файл не создан: {file_path}")
                        
                print(f"DEBUG: Паспорт создан: {passport_created}")
                print(f"DEBUG: Протокол 7 создан: {protocol_7_created}")
                print(f"DEBUG: Протокол 28 создан: {protocol_28_created}")
                
                if passport_created and protocol_7_created and protocol_28_created:
                    print("✓ Все файлы COMBO созданы успешно")
                else:
                    print("✗ Не все файлы COMBO созданы")
                    return False
            else:
                print("✗ Не удалось получить все файлы COMBO")
                return False
                
            # Проверяем, что записи сохранены в базе
            passports = db.get_passports()
            protocols = db.get_protocols()
            print(f"✓ Записи в БД - паспорта: {len(passports)}, протоколы: {len(protocols)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Ошибка при генерации COMBO: {e}")
            import traceback
            traceback.print_exc()
            return False
    finally:
        # Очищаем временные файлы
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Основная функция тестирования."""
    print("Запуск тестов генерации документов...")
    
    tests = [
        test_passport_generation,
        test_protocol_generation,
        test_combo_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Тест {test.__name__} завершился с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print(f"\n=== Результаты тестов ===")
    print(f"Пройдено: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ Все тесты прошли успешно!")
        return 0
    else:
        print("✗ Некоторые тесты не пройдены")
        return 1


if __name__ == "__main__":
    exit(main())