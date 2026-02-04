#!/usr/bin/env python3
"""
Test database module.
"""

from datetime import datetime
from core.database import DatabaseManager

def test_database():
    db = DatabaseManager()
    
    # Test save passport
    passport_data = {
        "number": "17-000045690",
        "firm": "ООО Тест",
        "address": "Тест адрес",
        "grade": "В15",
        "volume": 10.5,
        "pour_date": "2025-02-02",
        "object_name": "Тест объект",
        "network_name": "Тест сеть"
    }
    
    saved_number = db.save_passport(passport_data)
    print(f"Saved passport: {saved_number}")
    
    # Test get passports
    passports = db.get_passports()
    print(f"Total passports: {len(passports)}")
    
    # Test duplicates check
    duplicates = db.get_passports_by_date("2025-02-02")
    print(f"Passports on 2025-02-02: {duplicates}")

if __name__ == "__main__":
    test_database()