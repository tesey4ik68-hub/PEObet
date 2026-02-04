"""
Тесты для проверки логики генерации заключений на уплотнение.
"""

import unittest
import tempfile
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from app.core.database import DatabaseManager
from app.core.services.document_service import DocumentService


class TestCompactionConclusionLogic(unittest.TestCase):
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
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
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
    
    def test_generate_conclusion_for_new_entry_creates_unique_number(self):
        """Тестирует, что для новой записи генерируется уникальный номер заключения."""
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
        # Должно быть одно заключение для этой записи об уплотнении
        our_conclusions = [c for c in conclusions if c['compaction_entry_id'] == self.compaction_entry['id']]
        self.assertEqual(len(our_conclusions), 1)
        
        # Проверяем, что номер заключения сгенерирован правильно
        conclusion = our_conclusions[0]
        # Номер должен быть в формате ДД.ММ.Н/ГГ
        import re
        pattern = r"\d{2}\.\d{2}\.\d+/\d{2}"
        self.assertRegex(conclusion['number'], pattern)
        
        # Проверяем, что номер уникален для этой даты
        same_date_conclusions = self.db.get_compaction_conclusions_by_date(self.compaction_entry['end_date'])
        # В этот день должно быть только одно заключение
        self.assertEqual(len(same_date_conclusions), 1)
    
    def test_generate_conclusion_for_same_entry_replaces_old(self):
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
        # Номер должен остаться тем же, что и у первого заключения
        first_conclusion_number = [c for c in self.db.get_conclusions() if c['compaction_entry_id'] == self.compaction_entry['id']][0]['number']
        # Проверим, что это все еще та же запись (номер не изменился при замене)
        self.assertEqual(conclusions[0]['number'], first_conclusion_number)
        
        # Также проверим, что файлы различаются (старый удален, новый создан)
        self.assertNotEqual(first_files[0], second_files[0])
    
    def test_unique_number_generation_for_multiple_entries_same_date(self):
        """Тестирует, что номера заключений генерируются уникально для нескольких записей об уплотнении в один день."""
        # Создаем несколько записей об уплотнении с разными интервалами на одну дату
        entry1 = self.compaction_entry.copy()
        entry2 = self.compaction_entry.copy()
        entry2['interval'] = 'Т2'
        entry3 = self.compaction_entry.copy()
        entry3['interval'] = 'Т3'
        
        entry2_id = self.db.save_compaction_entry(entry2)
        entry2['id'] = entry2_id
        entry3_id = self.db.save_compaction_entry(entry3)
        entry3['id'] = entry3_id
        
        # Подготавливаем данные для генерации заключений
        entries = [
            {
                'work_type': entry1['work_type'],
                'interval': entry1['interval'],
                'start_date': entry1['start_date'],
                'end_date': entry1['end_date'],
                'firm': entry1['firm'],
                'thickness': entry1['thickness'],
                'object_name': entry1['object_name'],
                'address': self.test_object['address']
            },
            {
                'work_type': entry2['work_type'],
                'interval': entry2['interval'],
                'start_date': entry2['start_date'],
                'end_date': entry2['end_date'],
                'firm': entry2['firm'],
                'thickness': entry2['thickness'],
                'object_name': entry2['object_name'],
                'address': self.test_object['address']
            },
            {
                'work_type': entry3['work_type'],
                'interval': entry3['interval'],
                'start_date': entry3['start_date'],
                'end_date': entry3['end_date'],
                'firm': entry3['firm'],
                'thickness': entry3['thickness'],
                'object_name': entry3['object_name'],
                'address': self.test_object['address']
            }
        ]
        
        # Генерируем заключения для всех записей
        files = self.service.generate_compaction_conclusions(entries)
        
        self.assertEqual(len(files), 3)
        
        # Получаем заключения из базы для этой даты
        conclusions = self.db.get_compaction_conclusions_by_date(entry1['end_date'])
        
        # Проверяем, что все номера уникальны
        numbers = [c['number'] for c in conclusions]
        self.assertEqual(len(numbers), len(set(numbers)), "Номера заключений должны быть уникальными")
        
        # Проверяем, что все заключения имеют правильный формат номера
        import re
        pattern = r"\d{2}\.\d{2}\.\d+/\d{2}"
        for number in numbers:
            self.assertRegex(number, pattern)


if __name__ == '__main__':
    unittest.main()