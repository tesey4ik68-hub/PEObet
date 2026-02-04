"""
Сервис для генерации документов.
"""

from pathlib import Path
from datetime import datetime
from datetime import timedelta
from typing import Dict, List, Optional
from enum import Enum

from ..database import DatabaseManager
from ..numbering import generate_passport_number, generate_protocol_number
from ..calculations import get_grade_full_name, get_required_strength_28, generate_strength_28, generate_mass1, generate_mass2, generate_mass3, calculate_destroying_load, generate_destroying_load_variation, generate_strength_variation, calculate_average, to_float, generate_density, calculate_destroying_load_7days, generate_compaction_measurements, calculate_compaction_coefficient
from ..docx_engine import generate_document
from ..paths import TEMPLATES_DIR, DATA_DIR, DOCUMENTS_DIR, PASSPORTS_DIR, PROTOCOLS_DIR


class DocumentType(Enum):
    """Типы документов."""
    PASSPORT = "passport"
    PROTOCOL_7 = "protocol_7"
    PROTOCOL_28 = "protocol_28"
    COMBO = "combo"


class LabType(Enum):
    """Типы лабораторий."""
    LIK = "LIK"
    PTS = "PTS"


class DocumentService:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.output_dir = Path("Документы")
        self.last_generated_folder = None

    def generate_documents(
        self,
        entries: List[Dict],
        doc_type: DocumentType,
        lab_type: Optional[LabType] = None
    ) -> List[Path]:
        """
        Генерирует документы для указанных записей.
        
        Args:
            entries: Список записей с данными
            doc_type: Тип документа для генерации
            lab_type: Тип лаборатории (для протоколов)
            
        Returns:
            Список путей к сгенерированным файлам
        """
        generated_files = []

        # Создаем папки для сохранения
        timestamp = datetime.now().strftime('%d.%m.%Y %H-%M')
        
        from ..paths import PASSPORTS_DIR, PROTOCOLS_DIR
        
        # Для COMBO создаем обе папки
        if doc_type == DocumentType.COMBO:
            passport_folder = PASSPORTS_DIR / timestamp
            protocol_folder = PROTOCOLS_DIR / timestamp
            passport_folder.mkdir(parents=True, exist_ok=True)
            protocol_folder.mkdir(parents=True, exist_ok=True)
            self.last_generated_folder = protocol_folder  # Для открытия папки используем папку протоколов
        else:
            if doc_type == DocumentType.PASSPORT:
                folder = PASSPORTS_DIR / timestamp
            else:
                folder = PROTOCOLS_DIR / timestamp
            folder.mkdir(parents=True, exist_ok=True)
            self.last_generated_folder = folder

        for entry in entries:
            if doc_type == DocumentType.PASSPORT:
                file_path = self._generate_passport(entry, folder)
                generated_files.append(file_path)
            elif doc_type in [DocumentType.PROTOCOL_7, DocumentType.PROTOCOL_28]:
                file_path = self._generate_protocol(entry, doc_type, lab_type, folder)
                generated_files.append(file_path)
            elif doc_type == DocumentType.COMBO:
                # Генерируем паспорт в папку паспортов
                passport_path = self._generate_passport(entry, passport_folder)
                generated_files.append(passport_path)
                
                # Генерируем протоколы в папку протоколов
                protocol_7_path = self._generate_protocol(entry, DocumentType.PROTOCOL_7, lab_type, protocol_folder)
                generated_files.append(protocol_7_path)
                
                protocol_28_path = self._generate_protocol(entry, DocumentType.PROTOCOL_28, lab_type, protocol_folder)
                generated_files.append(protocol_28_path)

        return generated_files

    def _generate_passport(self, entry: Dict, folder: Path) -> Path:
        """Генерирует паспорт."""
        # Получаем дату заливки для генерации номера
        pour_date = datetime.strptime(entry['pour_date'], '%Y-%m-%d').date()
        
        # Получаем существующие номера для этой даты
        existing = self.db.get_passports_by_date(entry['pour_date'])
        number = generate_passport_number(pour_date, existing)
        
        # Подготовка данных для шаблона
        grade_full_name = get_grade_full_name(entry['grade'])
        
        months = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        
        # Валидация обязательных полей
        # Для COMBO данные уже передаются из tab_beton.py, но для других случаев проверяем
        firm = entry.get('firm', '')
        address = entry.get('address', '')
        if not firm or not address:
            # Попробуем получить данные из базы, если они не переданы
            # Это может быть необходимо для COMBO, где данные могут быть не в entry
            print(f"DEBUG: Missing firm or address in entry: {entry}")  # Для отладки
            raise ValueError("Некорректные данные записи для генерации паспорта: отсутствуют фирма или адрес")
        
        # Генерируем случайное время от 10:00 до 18:00
        import random
        hour = random.randint(10, 18)
        minute = random.randint(0, 59)
        time_str = f"{hour:02d}:{minute:02d}"
        
        doc_data = {
            "Нпаспорта": number,
            "фирма": firm,
            "адрес": address,
            "марка": grade_full_name,
            "марка2": entry['grade'],
            "объем": str(entry['volume']).replace('.', ','),
            "день_п": pour_date.strftime("%d"),
            "месяц_п": months[pour_date.month],
            "год_п": pour_date.strftime("%Y"),
            "дата_п": pour_date.strftime("%d.%m.%Y"),
            "время_п": time_str,
            "объект": entry.get('object_name', ''),
            "день_п3": pour_date.strftime("%d"),
            "месяц_п3": months[pour_date.month],
            "год_п3": pour_date.strftime("%Y"),
            "треб_проч_28_2": str(get_required_strength_28(entry['grade'])).replace('.', ',')
        }

        # Путь к файлу - изменен формат имени файла
        file_path = folder / f"Паспорт_{number}_от_{pour_date.strftime('%d.%m.%Y')}.docx"
        
        # Генерация документа
        if entry['grade'].startswith("Раствор"):
            template_path = TEMPLATES_DIR / "Шаблон раствор.docx"
        else:
            template_path = TEMPLATES_DIR / "Шаблон бетон.docx"
        try:
            print(f"DEBUG: Start passport generation")
            print(f"DEBUG: Entry = {entry}")
            print(f"DEBUG: Grade = {entry['grade']}, Number = {number}")
            print(f"DEBUG: Template = {template_path}")
            print(f"DEBUG: Output = {file_path}")
            print(f"DEBUG: Doc data keys = {list(doc_data.keys())}")
            generate_document(template_path, doc_data, file_path)
            print(f"DEBUG: Passport {number} generated successfully")
        except Exception as e:
            print(f"ERROR: Failed to generate passport {number}: {str(e)}")
            raise e
        
        # Сохраняем в базу
        passport_data = {
            "number": number,
            "firm": entry['firm'],
            "address": entry['address'],
            "grade": entry['grade'],
            "volume": entry['volume'],
            "pour_date": entry['pour_date'],
            "object_name": entry['object_name'],
            "network_name": entry['network']
        }
        try:
            self.db.save_passport(passport_data)
            print(f"DEBUG: Passport {number} saved to DB")
        except Exception as e:
            print(f"ERROR: Failed to save passport {number} to DB: {str(e)}")
            raise e
        return file_path

    def _generate_protocol(self, entry: Dict, protocol_type: DocumentType, lab_type: LabType, folder: Path) -> Path:
        """Генерирует протокол."""
        # Защитная валидация
        if lab_type is None:
            raise ValueError("Некорректные данные записи для генерации протокола: отсутствует тип лаборатории")
        
        firm = entry.get('firm', '')
        address = entry.get('address', '')
        object_name = entry.get('object_name', '')
        if not firm or not address or not object_name:
            raise ValueError("Некорректные данные записи для генерации протокола: отсутствуют фирма, адрес или название объекта")
        
        # Определяем возраст для протокола
        age_days = 7 if protocol_type == DocumentType.PROTOCOL_7 else 28
        
        # Генерируем номер протокола
        pour_date = datetime.strptime(entry['pour_date'], '%Y-%m-%d').date()
        test_date = pour_date + timedelta(days=age_days)
        # Получаем существующие номера для этой даты
        existing = self.db.get_protocols_by_date(test_date.strftime('%Y-%m-%d')) if hasattr(self.db, 'get_protocols_by_date') else []
        number = generate_protocol_number(pour_date, age_days, existing)
        
        # Определяем шаблон в зависимости от типа материала и лаборатории
        if lab_type == LabType.LIK:
            template_name = "Протокол.docx"
        else:  # PTS
            template_name = "Протокол 2.docx"
        
        # Подготовка данных для шаблона
        from random import randint, uniform
        import random

        # Получаем требуемую прочность на 28 дней
        required_strength_28 = to_float(get_required_strength_28(entry['grade']))
        required_strength = round(to_float(required_strength_28) * 0.7, 2) if age_days == 7 else round(to_float(required_strength_28), 2)
        # Генерируем фактические значения
        strength_28 = generate_strength_28(entry['grade'])
        density = generate_density(entry['grade'])  # Используем правильную функцию для получения плотности
        mass1 = to_float(generate_mass1(density))  # Масса 1
        mass2 = to_float(generate_mass2(mass1))    # Масса 2
        mass3 = to_float(generate_mass3(mass2))    # Масса 3

        # Добавим логирование для отладки
        print(f"DEBUG: Start protocol generation")
        print(f"DEBUG: Entry = {entry}")
        print(f"DEBUG: Grade = {entry['grade']}, Age = {age_days}, Number = {number}")
        print(f"DEBUG: Template = {TEMPLATES_DIR / template_name}")
        print(f"DEBUG: Output = {folder / f'протокол_{number}.docx'}")
        print(f"DEBUG: grade={entry['grade']}, required_strength_28={required_strength_28}, required_strength={required_strength}")
        print(f"DEBUG: strength_28={strength_28}, density={density}, mass1={mass1}, mass2={mass2}, mass3={mass3}")
        
        # Разрушающая нагрузка
        destroying_load = calculate_destroying_load(strength_28)
        destroying_load2 = generate_destroying_load_variation(destroying_load)
        destroying_load3 = generate_destroying_load_variation(destroying_load)
        
        # Для 7-дневных протоколов применяем специальное вычисление разрушающей нагрузки
        if age_days == 7:
            destroying_load = calculate_destroying_load_7days(strength_28)
            destroying_load2 = calculate_destroying_load_7days(strength_28)
            destroying_load3 = calculate_destroying_load_7days(strength_28)
        
        # Прочность
        strength1 = round(strength_28 * 0.7, 2) if age_days == 7 else round(strength_28, 2)
        strength2 = generate_strength_variation(strength1)
        strength3 = generate_strength_variation(strength1)
        avg_strength = round((strength1 + strength2 + strength3) / 3, 2)
        
        # Средняя плотность
        avg_density = round((mass1 + mass2 + mass3) / 3, 2)
        
        # Месяцы на русском
        months = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        
        # Дата паспорта (дата заливки + 1 день)
        passport_date = pour_date + timedelta(days=1)
        
        doc_data = {
        # Основные данные
        # Исправленный формат номера протокола: используем уже сформированный номер из generate_protocol_number
        "Нпротокол": number,
            "марка2": entry['grade'],
            "год": test_date.strftime('%Y'),
            "треб_проч": str(required_strength).replace('.', ','),
            "участок": entry['area'],
            "фирма": entry['firm'],
            "объект": entry['object_name'],
            "день_б": pour_date.strftime('%d'),
            "месяц_б": months[pour_date.month],
            "год_б": pour_date.strftime('%Y'),
            "день_и": test_date.strftime('%d'),
            "месяц_и": months[test_date.month],
            "год_и": test_date.strftime('%Y'),
            "возраст": str(age_days),
            "день_п": passport_date.strftime('%d'),
            "месяц_п": months[passport_date.month],
            "год_п": passport_date.strftime('%Y'),
            
            # Данные для таблицы
            "масса1": str(mass1).replace('.', ','),
            "масса2": str(mass2).replace('.', ','),
            "масса3": str(mass3).replace('.', ','),
            "плотн1": str(mass1).replace('.', ','),
            "плотн2": str(mass2).replace('.', ','),
            "плотн3": str(mass3).replace('.', ','),
            "ср_плотн": str(avg_density).replace('.', ','),
            "раз_нагр_1": str(destroying_load).replace('.', ','),
            "раз_нагр_2": str(destroying_load2).replace('.', ','),
            "раз_нагр_3": str(destroying_load3).replace('.', ','),
            "проч_1": str(strength1).replace('.', ','),
            "проч_2": str(strength2).replace('.', ','),
            "проч_3": str(strength3).replace('.', ','),
            "ср_проч": str(avg_strength).replace('.', ',')
        }

        # Путь к файлу - изменен формат имени файла для протоколов
        # Заменяем / на - в номере для совместимости с Windows
        safe_number = number.replace("/", "-")
        if age_days == 7:
            file_name = f"Акт № {safe_number} от {test_date.strftime('%d.%m.%Y')}.docx"
        else:  # 28 дней
            file_name = f"Акт № {safe_number} от {test_date.strftime('%d.%m.%Y')}.docx"
        file_path = folder / file_name
        
        # Генерация документа
        template_path = TEMPLATES_DIR / template_name
        generate_document(template_path, doc_data, file_path)
        print(f"DEBUG: Protocol {number} generated successfully")
        
        # Сохраняем в базу
        protocol_data = {
            "number": number,
            "grade": entry['grade'],
            "required_strength": required_strength,
            "participant": entry['firm'],
            "object_name": entry['object_name'],
            "network_name": entry['network'],
            "pour_date": entry['pour_date'],
            "test_date": test_date.strftime('%Y-%m-%d'),
            "age_days": age_days,
            "passport_number": "",  # номер паспорта
        }
        self.db.save_protocol(protocol_data)
        
        return file_path

    def generate_compaction_conclusions(self, entries: List[Dict]) -> List[Path]:
        """
        Генерирует заключения на уплотнение для указанных записей.
        
        Args:
            entries: Список записей с данными
            
        Returns:
            Список путей к сгенерированным файлам
        """
        generated_files = []

        # Создаем папку для сохранения
        timestamp = datetime.now().strftime('%d.%m.%Y %H-%M')
        folder = DOCUMENTS_DIR / "Заключения" / timestamp
        folder.mkdir(parents=True, exist_ok=True)
        self.last_generated_folder = folder

        for entry in entries:
            # Получаем ID записи об уплотнении
            compaction_entry_id = self._find_compaction_entry_id(entry)
            if compaction_entry_id is None:
                print(f"DEBUG: Запись об уплотнении не найдена для параметров: {entry}")
                raise ValueError("Запись об уплотнении не найдена в базе данных")
            
            # Генерируем заключение
            file_path = self.generate_compaction_conclusion(compaction_entry_id, replace_existing=False)
            generated_files.append(file_path)

        return generated_files


    def _generate_compaction_conclusion_number(self, end_date: datetime.date, existing: List[str]) -> str:
        """
        Генерирует номер заключения на уплотнение.
        
        Формат: ДД.ММ.Н/ГГ
        где Н - порядковый номер заключения в этот день
        """
        print(f"DEBUG: Генерация номера для даты {end_date}, существующие: {existing}")
        
        # Форматируем дату
        date_part = end_date.strftime("%d.%m")
        year_part = end_date.strftime("%y")
        
        # Считаем количество существующих заключений в этот день
        count = len(existing) + 1
        
        number = f"{date_part}.{count}/{year_part}"
        print(f"DEBUG: Сгенерирован номер: {number}")
        return number

    def _generate_compaction_conclusion_number_with_check(self, end_date: datetime.date, existing_on_date: List[str]) -> str:
        """
        Генерирует номер заключения на уплотнение с проверкой на уникальность среди всех заключений на эту дату.
        
        Формат: ДД.ММ.Н/ГГ
        где Н - порядковый номер заключения в этот день
        """
        print(f"DEBUG: Генерация номера с проверкой для даты {end_date}, существующие на дату: {existing_on_date}")
        
        # Форматируем дату
        date_part = end_date.strftime("%d.%m")
        year_part = end_date.strftime("%y")
        
        # Находим максимальный номер среди существующих заключений на эту дату
        max_num = 0
        for num_str in existing_on_date:
            try:
                # Извлекаем номер из строки формата ДД.ММ.Н/ГГ
                parts = num_str.split('.')
                if len(parts) >= 2:
                    num_part = parts[1].split('/')[0]  # Берем часть до /
                    num = int(num_part)
                    if num > max_num:
                        max_num = num
            except (ValueError, IndexError):
                continue  # Если формат не распознан, пропускаем
        
        # Новый номер - следующий за максимальным
        new_num = max_num + 1
        number = f"{date_part}.{new_num}/{year_part}"
        print(f"DEBUG: Сгенерирован уникальный номер: {number}")
        return number

    def _find_compaction_entry_id(self, entry: Dict) -> Optional[int]:
        """
        Находит ID записи об уплотнении по параметрам.
        """
        print(f"DEBUG: Поиск ID записи об уплотнении по параметрам: {entry}")
        # Получаем все записи об уплотнении для данного объекта
        entries = self.db.get_compaction_entries_by_object(entry['object_name'])
        print(f"DEBUG: Найдено записей для объекта {entry['object_name']}: {len(entries)}")
        
        # Ищем запись с совпадающими параметрами
        for comp_entry in entries:
            if (comp_entry['work_type'] == entry['work_type'] and
                comp_entry['interval'] == entry['interval'] and
                comp_entry['start_date'] == entry['start_date'] and
                comp_entry['end_date'] == entry['end_date'] and
                comp_entry['firm'] == entry['firm'] and
                float(comp_entry['thickness']) == float(entry['thickness'])):
                print(f"DEBUG: Найдено совпадение, ID: {comp_entry['id']}")
                return comp_entry['id']
        
        print(f"DEBUG: Запись об уплотнении не найдена")
        return None

    def open_last_folder(self):
        """Открывает последнюю папку с документами."""
        if self.last_generated_folder and self.last_generated_folder.exists():
            import subprocess
            import sys
            
            if sys.platform == "win32":
                subprocess.run(["explorer", str(self.last_generated_folder)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.last_generated_folder)])
            else:
                subprocess.run(["xdg-open", str(self.last_generated_folder)])
