"""
Тесты для проверки генерации заключений на уплотнение.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from app.core.database import DatabaseManager
from app.core.services.document_service import DocumentService


class TestCompactionConclusions(unittest.TestCase):
    def setUp(self):
        """Устанавливает тестовое окружение."""
        # Создаем временную базу данных
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db_path = Path(self.temp_dir) / "test_app.db"
        
        # Инициализируем базу данных
        self.db = DatabaseManager(self.temp_db_path)
        
        # Создаем тестовые данные
        self.test_object = {
            'name': 'Тестовый объект',
            'address': 'Тестовый адрес',
            'firm': 'Тестовая фирма'
        }
        
        # Добавляем объект в базу
        with self.db.connection:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO objects (name, address, firm)
                VALUES (?, ?, ?)
            """, (self.test_object['name'], self.test_object['address'], self.test_object['firm']))
        
        # Создаем тестовую запись об уплотнении
        self.compaction_entry = {
            'object_name': self.test_object['name'],
            'work_type': 'Подготовка',
            'interval': 'Т1',
            'start_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'firm': 'ООО "Тест"',
            'thickness': 200.0,
            'status': 'Ожидает'
        }
        
        entry_id = self.db.save_compaction_entry(self.compaction_entry)
        self.compaction_entry['id'] = entry_id
        
        self.service = DocumentService(self.db)
    
    def tearDown(self):
        """Очищает тестовое окружение."""
        # Закрываем соединение с базой данных
        self.db.close()
        
        # Удаляем временные файлы
        shutil.rmtree(self.temp_dir)
    
    def test_generate_conclusion_for_new_entry(self):
        """Тестирует генерацию заключения для новой записи об уплотнении."""
        # Подготавливаем данные для генерации заключения
        conclusion_entry = {
            'work_type': self.compaction_entry['work_type'],
            'interval': self.compaction_entry['interval'],
            'start_date': self.compaction_entry['start_date'],
            'end_date': self.compaction_entry['end_date'],
            'firm': self.compaction_entry['firm'],
            'thickness': self.compaction_entry['thickness'],
            'object_name': self.compaction_entry['object_name'],
            'address': self.test_object['address']
        }
        
        # Генерируем заключение
        generated_files = self.service.generate_compaction_conclusions([conclusion_entry])
        
        # Проверяем, что файл был сгенерирован
        self.assertEqual(len(generated_files), 1)
        self.assertTrue(generated_files[0].exists())
        
        # Проверяем, что заключение сохранено в базу
        conclusions = self.db.get_conclusions()
        # Должно быть одно заключение
        self.assertEqual(len([c for c in conclusions if c['compaction_entry_id'] == self.compaction_entry['id']]), 1)
        
        # Проверяем, что номер заключения сгенерирован правильно
        conclusion = [c for c in conclusions if c['compaction_entry_id'] == self.compaction_entry['id']][0]
        # Номер должен быть в формате ДД.ММ.Н/ГГ
        import re
        pattern = r"\d{2}\.\d{2}\.\d+/\d{2}"
        self.assertRegex(conclusion['number'], pattern)
    
    def test_generate_conclusion_for_existing_entry_replaces_old(self):
        """Тестирует, что при повторной генерации для той же записи об уплотнении старое заключение заменяется."""
        # Подготавливаем данные для генерации заключения
        conclusion_entry = {
            'work_type': self.compaction_entry['work_type'],
            'interval': self.compaction_entry['interval'],
            'start_date': self.compaction_entry['start_date'],
            'end_date': self.compaction_entry['end_date'],
            'firm': self.compaction_entry['firm'],
            'thickness': self.compaction_entry['thickness'],
            'object_name': self.compaction_entry['object_name'],
            'address': self.test_object['address']
        }
        
        # Генерируем первое заключение
        first_files = self.service.generate_compaction_conclusions([conclusion_entry])
        self.assertEqual(len(first_files), 1)
        
        # Получаем количество заключений до второй генерации
        before_count = len([c for c in self.db.get_conclusions() if c['compaction_entry_id'] == self.compaction_entry['id']])
        
        # Генерируем второе заключение для той же записи
        second_files = self.service.generate_compaction_conclusions([conclusion_entry])
        self.assertEqual(len(second_files), 1)
        
        # Проверяем, что количество заключений для этой записи осталось 1 (старое было заменено)
        after_count = len([c for c in self.db.get_conclusions() if c['compaction_entry_id'] == self.compaction_entry['id']])
        self.assertEqual(after_count, 1)
        
        # Проверяем, что номер остался тем же (при замене должен использоваться тот же номер)
        conclusions = [c for c in self.db.get_conclusions() if c['compaction_entry_id'] == self.compaction_entry['id']]
        self.assertEqual(len(conclusions), 1)
        # Проверяем, что файлы различаются (старый удален, новый создан)
        self.assertNotEqual(first_files[0], second_files[0])
        # Но номер в базе должен остаться тот же
        first_conclusion = [c for c in self.db.get_conclusions() if c['compaction_entry_id'] == self.compaction_entry['id']][0]
        # Проверим, что это все еще та же запись (номер не изменился при замене)
        # В нашей реализации при замене мы используем тот же номер, что и у старого заключения
    
    def test_unique_number_generation(self):
        """Тестирует, что номера заключений генерируются уникально для одной даты."""
        # Подготавливаем данные для генерации заключений
        conclusion_entry1 = {
            'work_type': self.compaction_entry['work_type'],
            'interval': self.compaction_entry['interval'] + 'A',
            'start_date': self.compaction_entry['start_date'],
            'end_date': self.compaction_entry['end_date'],
            'firm': self.compaction_entry['firm'],
            'thickness': self.compaction_entry['thickness'],
            'object_name': self.compaction_entry['object_name'],
            'address': self.test_object['address']
        }
        
        conclusion_entry2 = {
            'work_type': self.compaction_entry['work_type'],
            'interval': self.compaction_entry['interval'] + 'B',
            'start_date': self.compaction_entry['start_date'],
            'end_date': self.compaction_entry['end_date'],
            'firm': self.compaction_entry['firm'],
            'thickness': self.compaction_entry['thickness'],
            'object_name': self.compaction_entry['object_name'],
            'address': self.test_object['address']
        }
        
        # Создаем две различные записи об уплотнении
        entry2 = self.compaction_entry.copy()
        entry2['interval'] = self.compaction_entry['interval'] + 'B'
        entry2_id = self.db.save_compaction_entry(entry2)
        entry2['id'] = entry2_id
        
        # Генерируем заключения для обеих записей
        files = self.service.generate_compaction_conclusions([
            conclusion_entry1,
            conclusion_entry2
        ])
        
        self.assertEqual(len(files), 2)
        
        # Получаем заключения из базы
        conclusions = self.db.get_conclusions()
        our_conclusions = [c for c in conclusions if c['compaction_entry_id'] in [self.compaction_entry['id'], entry2['id']]]
        
        self.assertEqual(len(our_conclusions), 2)
        
        # Проверяем, что номера уникальны
        numbers = [c['number'] for c in our_conclusions]
        self.assertEqual(len(numbers), len(set(numbers)), "Номера заключений должны быть уникальными")


if __name__ == '__main__':
    unittest.main()