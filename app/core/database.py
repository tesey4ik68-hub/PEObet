"""
Модуль базы данных с использованием SQLite для локального хранения.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path: Path = None):
        if db_path is None:
            from core.paths import DATA_DIR
            db_path = DATA_DIR / "app.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
        print(f"DEBUG: DatabaseManager initialized with db_path: {self.db_path}")
    
    def close(self):
        """Закрывает соединение с базой данных."""
        print(f"DEBUG: DatabaseManager closed connection to {self.db_path}")

    def init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Objects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    firm TEXT,
                    UNIQUE(name, address)
                )
            """)
            # Проверяем, есть ли колонка firm, если нет - добавляем
            try:
                cursor.execute("PRAGMA table_info(objects)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                if 'firm' not in column_names:
                    cursor.execute("ALTER TABLE objects ADD COLUMN firm TEXT")
                    print("DEBUG: Added 'firm' column to objects table")
            except Exception as e:
                print(f"DEBUG: Error checking/adding 'firm' column: {e}")

            # Проверяем, есть ли колонка end_date в conclusions, если нет - добавляем
            try:
                cursor.execute("PRAGMA table_info(conclusions)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                if 'end_date' not in column_names:
                    cursor.execute("ALTER TABLE conclusions ADD COLUMN end_date TEXT")
                    print("DEBUG: Added 'end_date' column to conclusions table")
            except Exception as e:
                print(f"DEBUG: Error checking/adding 'end_date' column: {e}")

            # Passports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT UNIQUE,
                    firm TEXT,
                    address TEXT,
                    grade TEXT,
                    volume REAL,
                    pour_date TEXT,
                    object_name TEXT,
                    network_name TEXT,
                    created_at TEXT
                )
            """)

            # Protocols table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS protocols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT UNIQUE,
                    grade TEXT,
                    required_strength REAL,
                    participant TEXT,
                    object_name TEXT,
                    network_name TEXT,
                    pour_date TEXT,
                    test_date TEXT,
                    age_days INTEGER,
                    passport_number TEXT,
                    created_at TEXT
                )
            """)

            # Conclusions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conclusions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT UNIQUE,
                    compaction_entry_id INTEGER,
                    firm TEXT,
                    object_name TEXT,
                    address TEXT,
                    work_date_range TEXT,
                    layer_thickness TEXT,
                    num_layers INTEGER,
                    created_at TEXT,
                    end_date TEXT
                )
            """)

            # Concrete entries table (for beton records)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concrete_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_name TEXT NOT NULL,
                    grade TEXT NOT NULL,
                    volume REAL NOT NULL,
                    pour_date TEXT NOT NULL,
                    network TEXT,
                    area TEXT NOT NULL,
                    status TEXT DEFAULT 'Ожидает',
                    created_at TEXT
                )
            """)

            # Compaction entries table (for уплотнение records)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compaction_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_name TEXT NOT NULL,
                    work_type TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    firm TEXT NOT NULL,
                    thickness REAL NOT NULL,
                    status TEXT DEFAULT 'Ожидает'
                )
            """)

            # Journal tables (simplified)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_general (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    work TEXT,
                    participant TEXT,
                    object_name TEXT,
                    network_name TEXT,
                    created_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_input (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material TEXT,
                    batch TEXT,
                    date TEXT,
                    participant TEXT,
                    object_name TEXT,
                    network_name TEXT,
                    works TEXT,
                    created_at TEXT
                )
            """)

            conn.commit()

    def save_passport(self, data: Dict) -> str:
        """Сохраняет паспорт и возвращает номер."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO passports (number, firm, address, grade, volume, pour_date, object_name, network_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["number"], data["firm"], data["address"], data["grade"], data["volume"],
                data["pour_date"], data["object_name"], data["network_name"], datetime.now().isoformat()
            ))
            conn.commit()
            return data["number"]

    def get_passports(self) -> List[Dict]:
        """Получает все паспорта."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM passports ORDER BY created_at DESC")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def save_protocol(self, data: Dict) -> str:
        """Сохраняет протокол и возвращает номер."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO protocols (number, grade, required_strength, participant, object_name, network_name, pour_date, test_date, age_days, passport_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["number"], data["grade"], data["required_strength"], data["participant"],
                data["object_name"], data["network_name"], data["pour_date"], data["test_date"],
                data["age_days"], data["passport_number"], datetime.now().isoformat()
            ))
            conn.commit()
            return data["number"]

    def get_protocols(self) -> List[Dict]:
        """Получает все протоколы."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM protocols ORDER BY created_at DESC")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def save_conclusion(self, data: Dict) -> str:
        """Сохраняет заключение и возвращает номер."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conclusions (number, compaction_entry_id, firm, object_name, address, work_date_range, layer_thickness, num_layers, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["number"], data["compaction_entry_id"], data["firm"], data["object_name"], data["address"],
                data["work_date_range"], data["layer_thickness"], data["num_layers"],
                data["end_date"], datetime.now().isoformat()
            ))
            conn.commit()
            return data["number"]

    def get_conclusions(self) -> List[Dict]:
        """Получает все заключения."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conclusions ORDER BY created_at DESC")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_passports_by_date(self, date_str: str) -> List[str]:
        """Получает номера паспортов для указанной даты для проверки дубликатов."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT number FROM passports WHERE pour_date = ?", (date_str,))
            return [row[0] for row in cursor.fetchall()]

    def get_protocols_by_date(self, date_str: str) -> List[str]:
        """Получает номера протоколов для указанной даты для проверки дубликатов."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT number FROM protocols WHERE test_date = ?", (date_str,))
            return [row[0] for row in cursor.fetchall()]

    def get_conclusions_by_date(self, date_str: str) -> List[str]:
        """Получает номера заключений для указанной даты для проверки дубликатов."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT number FROM conclusions WHERE work_date_range LIKE ?", (f"%{date_str}%",))
            return [row[0] for row in cursor.fetchall()]

    def get_compaction_conclusions_by_date(self, date_str: str) -> List[str]:
        """Получает номера заключений на уплотнение для указанной даты для проверки дубликатов."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT number FROM conclusions WHERE end_date = ?", (date_str,))
            return [row[0] for row in cursor.fetchall()]
    
    def get_conclusion_by_compaction_entry(self, entry_id: int) -> Optional[Dict]:
        """Получает заключение по ID записи об уплотнении."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conclusions WHERE compaction_entry_id = ?", (entry_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_conclusions_by_compaction_entry(self, entry_id: int) -> List[Dict]:
        """Получает все заключения по ID записи об уплотнении."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conclusions WHERE compaction_entry_id = ?", (entry_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def delete_conclusion_by_id(self, conclusion_id: int):
        """Удаляет заключение по ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conclusions WHERE id = ?", (conclusion_id,))
            conn.commit()
    
    def get_compaction_entries_by_object(self, object_name: str) -> List[Dict]:
        """Получает записи об уплотнении для указанного объекта."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, work_type, interval, start_date, end_date, firm, thickness, status FROM compaction_entries WHERE object_name = ?",
                (object_name,)
            )
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def delete_records(self, table: str, ids: List[int]):
        """Удаляет записи по ID."""
        placeholders = ",".join(["?"] * len(ids))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
            conn.commit()

    def save_concrete_entry(self, data: Dict) -> int:
        """Сохраняет запись бетона и возвращает ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO concrete_entries (object_name, grade, volume, pour_date, network, area, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["object_name"], data["grade"], data["volume"], data["pour_date"],
                data["network"], data["area"], data["status"], datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def save_compaction_entry(self, data: Dict) -> int:
        """Сохраняет запись об уплотнении в базу данных."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compaction_entries (
                    object_name, work_type, interval, start_date, end_date, firm, thickness, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['object_name'], data['work_type'], data['interval'],
                data['start_date'], data['end_date'], data['firm'],
                data['thickness'], data['status']
            ))
            conn.commit()
            return cursor.lastrowid

    def get_concrete_entries(self, object_name: str) -> List[Dict]:
        """Получает все записи бетона для указанного объекта."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM concrete_entries 
                WHERE object_name = ?
                ORDER BY created_at DESC
            """, (object_name,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def update_concrete_entry_status(self, entry_id: int, status: str):
        """Обновляет статус записи бетона."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE concrete_entries 
                SET status = ?
                WHERE id = ?
            """, (status, entry_id))
            conn.commit()

    def delete_object_and_entries(self, object_name: str):
        """Удаляет объект и все связанные записи бетона."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Удаляем записи бетона для объекта
            cursor.execute("DELETE FROM concrete_entries WHERE object_name = ?", (object_name,))
            # Удаляем сам объект (если он есть в таблице objects)
            cursor.execute("DELETE FROM objects WHERE name = ?", (object_name,))
            conn.commit()
