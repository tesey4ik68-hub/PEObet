"""
Вкладка "Паспорта" для GUI.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QLabel, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from core.database import DatabaseManager
from core.numbering import generate_passport_number
from core.docx_engine import generate_document
from core.paths import TEMPLATES_DIR, PASSPORTS_DIR


class TabPassports(QWidget):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Форма ввода
        form_layout = QFormLayout()
        
        self.firm_input = QLineEdit()
        self.address_input = QLineEdit()
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["В7,5", "В15", "В20", "В22,5", "В25", "В30", "В35", "В40", "В50"])
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0, 999999)
        self.pour_date_input = QDateEdit()
        self.pour_date_input.setDate(QDate.currentDate())
        self.pour_date_input.setCalendarPopup(True)
        self.object_input = QLineEdit()
        self.network_input = QLineEdit()

        form_layout.addRow("Фирма:", self.firm_input)
        form_layout.addRow("Адрес:", self.address_input)
        form_layout.addRow("Марка:", self.grade_combo)
        form_layout.addRow("Объем:", self.volume_input)
        form_layout.addRow("Дата заливки:", self.pour_date_input)
        form_layout.addRow("Объект:", self.object_input)
        form_layout.addRow("Сеть:", self.network_input)

        # Кнопки и статус
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить в таблицу")
        self.add_btn.setStyleSheet("background-color: blue; color: white;")
        self.generate_selected_btn = QPushButton("Сформировать выбранные")
        self.generate_selected_btn.setStyleSheet("background-color: green; color: white;")
        self.status_label = QLabel("Статус: не сформирован")
        self.status_label.setStyleSheet("color: black;")
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.generate_selected_btn)
        button_layout.addWidget(self.status_label)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Номер", "Фирма", "Адрес", "Марка", "Объем", "Дата", "Объект", "Сеть"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # Сигналы
        self.add_btn.clicked.connect(self.add_passport_to_table)
        self.generate_selected_btn.clicked.connect(self.generate_selected_passports)
        self.load_passports()

    def load_passports(self):
        """Загружает паспорта в таблицу."""
        self.table.setRowCount(0)
        passports = self.db.get_passports()
        for p in passports:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p["number"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(p["firm"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(p["address"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(p["grade"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(p["volume"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(p["pour_date"])))
            self.table.setItem(row, 6, QTableWidgetItem(str(p["object_name"])))
            self.table.setItem(row, 7, QTableWidgetItem(str(p["network_name"])))

    def add_passport_to_table(self):
        """Добавляет паспорт в таблицу."""
        try:
            # Собираем данные
            firm = self.firm_input.text().strip()
            address = self.address_input.text().strip()
            grade = self.grade_combo.currentText()
            volume = self.volume_input.value()
            pour_date = self.pour_date_input.date().toPython()
            object_name = self.object_input.text().strip()
            network_name = self.network_input.text().strip()

            if not all([firm, address, grade, object_name, network_name]):
                raise ValueError("Заполните все обязательные поля")

            # Генерация номера
            existing = self.db.get_passports_by_date(pour_date.strftime("%Y-%m-%d"))
            number = generate_passport_number(pour_date, existing)

            # Сохранение в БД
            data = {
                "number": number,
                "firm": firm,
                "address": address,
                "grade": grade,
                "volume": volume,
                "pour_date": pour_date.strftime("%Y-%m-%d"),
                "object_name": object_name,
                "network_name": network_name
            }
            self.db.save_passport(data)

            # Обновление интерфейса
            self.status_label.setText(f"Добавлено в таблицу: №{number}")
            self.status_label.setStyleSheet("color: blue;")
            self.load_passports()

        except Exception as e:
            self.status_label.setText("Не добавлено")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении в таблицу: {str(e)}")

    def generate_selected_passports(self):
        """Генерирует выбранные паспорта из таблицы."""
        try:
            selected_rows = set()
            for item in self.table.selectedItems():
                selected_rows.add(item.row())

            if not selected_rows:
                QMessageBox.warning(self, "Предупреждение", "Выберите строки для генерации")
                return

            generated = []
            for row in selected_rows:
                number = self.table.item(row, 0).text()
                firm = self.table.item(row, 1).text()
                address = self.table.item(row, 2).text()
                grade = self.table.item(row, 3).text()
                volume = float(self.table.item(row, 4).text())
                pour_date_str = self.table.item(row, 5).text()
                object_name = self.table.item(row, 6).text()
                network_name = self.table.item(row, 7).text()

                # Преобразуем дату
                pour_date = datetime.strptime(pour_date_str, "%Y-%m-%d").date()

                # Проверим, есть ли уже такой паспорт в БД (для избежания дубликатов номеров)
                existing = self.db.get_passports_by_date(pour_date.strftime("%Y-%m-%d"))
                if number in existing:
                    # Используем существующий номер
                    pass
                else:
                    # Генерируем новый номер
                    number = generate_passport_number(pour_date, existing)
                    # Обновим в БД
                    data = {
                        "number": number,
                        "firm": firm,
                        "address": address,
                        "grade": grade,
                        "volume": volume,
                        "pour_date": pour_date.strftime("%Y-%m-%d"),
                        "object_name": object_name,
                        "network_name": network_name
                    }
                    self.db.save_passport(data)

                # Генерация DOCX
                template_path = TEMPLATES_DIR / "Шаблон бетон.docx"
                # Используем текущую дату и время для папки
                from datetime import datetime as dt
                current_dt = dt.now()
                folder = PASSPORTS_DIR / f"{current_dt.strftime('%d.%m.%Y %H-%M')}"
                folder.mkdir(parents=True, exist_ok=True)
                output_path = folder / f"паспорт_{number}.docx"

                # Получаем полное название марки бетона
                from core.calculations import get_grade_full_name, get_required_strength_28
                grade_full_name = get_grade_full_name(grade)
                required_strength_28_value = get_required_strength_28(grade)
                
                # Русские названия месяцев
                months = {
                    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
                    5: "мая", 6: "июня", 7: "июля", 8: "августа",
                    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
                }
                
                doc_data = {
                    "Нпаспорта": number,
                    "фирма": firm,
                    "адрес": address,
                    "марка": grade_full_name,
                    "марка2": grade,
                    "объем": str(volume).replace('.', ','),
                    "день_п": pour_date.strftime("%d"),
                    "месяц_п": months[pour_date.month],
                    "год_п": pour_date.strftime("%Y"),
                    "объект": object_name,
                    "день_п3": pour_date.strftime("%d"),
                    "месяц_п3": months[pour_date.month],
                    "год_п3": pour_date.strftime("%Y"),
                    "треб_проч_28_2": str(required_strength_28_value).replace('.', ',')
                }
                generate_document(template_path, doc_data, output_path)
                generated.append(number)

            self.status_label.setText(f"Создано документов: {', '.join(generated)}")
            self.status_label.setStyleSheet("color: green;")

        except Exception as e:
            self.status_label.setText("Документы не созданы")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации выбранных паспортов: {str(e)}")
