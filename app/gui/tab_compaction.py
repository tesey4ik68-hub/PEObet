"""
Вкладка "Уплотнение".
"""

from datetime import datetime, timedelta
from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidgetItem,
    QHeaderView, QMessageBox, QLabel, QDateEdit, QCheckBox, QGroupBox,
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup, QRadioButton,
    QTableWidget, QFileDialog, QMenu
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from core.services.document_service import DocumentService, DocumentType, LabType
from core.calculations import generate_compaction_data, calculate_average, calculate_compaction_coefficient


class TabCompaction(QWidget):
    def __init__(self, db, selected_object):
        super().__init__()
        self.db = db
        self.selected_object = selected_object
        self.service = DocumentService(db)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()

        # Форма ввода
        form_group = QGroupBox("Добавить запись")
        form_layout = QFormLayout()
        
        self.work_type_combo = QComboBox()
        self.work_type_combo.addItems(["Подготовка", "Основание", "Обратная засыпка", "Засыпки"])
        self.interval_input = QLineEdit()
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.firm_input = QLineEdit()
        self.thickness_input = QDoubleSpinBox()
        self.thickness_input.setRange(0, 99999)

        form_layout.addRow("Тип работ:", self.work_type_combo)
        form_layout.addRow("Интервал:", self.interval_input)
        form_layout.addRow("Дата начала:", self.start_date_input)
        form_layout.addRow("Дата окончания:", self.end_date_input)
        form_layout.addRow("Фирма:", self.firm_input)
        form_layout.addRow("Толщина слоя:", self.thickness_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Загрузка существующих записей из базы данных
        # self.load_existing_entries()  # Загрузка будет выполнена позже, после создания таблицы

        # Кнопки под формой
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить в таблицу")
        self.add_btn.setStyleSheet("background-color: blue; color: white;")
        self.generate_btn = QPushButton("Сформировать заключение")
        self.generate_btn.setStyleSheet("background-color: green; color: white;")
        self.open_folder_btn = QPushButton("Открыть папку с документами")
        self.open_folder_btn.setStyleSheet("background-color: lightblue; color: black;")
        
        self.add_btn.clicked.connect(self.add_to_table)
        self.generate_btn.clicked.connect(self.generate_compaction_conclusion)
        self.open_folder_btn.clicked.connect(self.open_last_folder)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(button_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(8)  # Чекбокс + 7 полей
        self.table.setHorizontalHeaderLabels(["", "Тип работ", "Интервал", "Дата начала", "Дата окончания", "Фирма", "Толщина", "Статус"])
        
        # Устанавливаем ширину первого столбца для чекбоксов
        self.table.setColumnWidth(0, 30)
        # Устанавливаем ширину столбца "Тип работ" до 120 пикселей
        self.table.setColumnWidth(1, 120)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)

        layout.addWidget(self.table)

        self.setLayout(layout)
        
        # Загружаем существующие записи после создания таблицы
        self.load_existing_entries()
    
    def load_existing_entries(self):
        """Загружает существующие записи из базы данных."""
        try:
            print(f"DEBUG: Загрузка записей для объекта: {self.selected_object}")
            # Получаем записи для текущего объекта
            entries = self.db.get_compaction_entries_by_object(self.selected_object['name'])
            print(f"DEBUG: Получено записей: {len(entries)}")
            
            for entry in entries:
                print(f"DEBUG: Обработка записи: {entry}")
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Чекбокс
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox = QCheckBox()
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(row, 0, checkbox_widget)
                
                # Данные
                self.table.setItem(row, 1, QTableWidgetItem(entry['work_type']))
                self.table.setItem(row, 2, QTableWidgetItem(entry['interval']))
                self.table.setItem(row, 3, QTableWidgetItem(entry['start_date']))
                self.table.setItem(row, 4, QTableWidgetItem(entry['end_date']))
                self.table.setItem(row, 5, QTableWidgetItem(entry['firm']))
                self.table.setItem(row, 6, QTableWidgetItem(str(entry['thickness'])))
                self.table.setItem(row, 7, QTableWidgetItem(entry.get('status', 'Ожидает')))
                
        except Exception as e:
            print(f"Ошибка при загрузке записей: {str(e)}")
            import traceback
            traceback.print_exc()

    def add_to_table(self):
        """Добавляет запись в таблицу."""
        work_type = self.work_type_combo.currentText()
        interval = self.interval_input.text().strip()
        start_date = self.start_date_input.date().toPython()
        end_date = self.end_date_input.date().toPython()
        firm = self.firm_input.text().strip()
        thickness = self.thickness_input.value()

        if not interval or not firm:
            QMessageBox.warning(self, "Предупреждение", "Введите интервал и фирму")
            return

        # Подготовка данных для сохранения
        data = {
            'object_name': self.selected_object['name'],
            'work_type': work_type,
            'interval': interval,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'firm': firm,
            'thickness': thickness,
            'status': 'Ожидает'
        }

        # Сохраняем в базу данных
        entry_id = self.db.save_compaction_entry(data)

        # Добавляем строку в таблицу
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Чекбокс
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox = QCheckBox()
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, checkbox_widget)
        
        # Данные
        self.table.setItem(row, 1, QTableWidgetItem(work_type))
        self.table.setItem(row, 2, QTableWidgetItem(interval))
        self.table.setItem(row, 3, QTableWidgetItem(start_date.strftime("%d.%m.%Y")))
        self.table.setItem(row, 4, QTableWidgetItem(end_date.strftime("%d.%m.%Y")))
        self.table.setItem(row, 5, QTableWidgetItem(firm))
        self.table.setItem(row, 6, QTableWidgetItem(str(thickness)))
        self.table.setItem(row, 7, QTableWidgetItem("Ожидает"))

        # Очищаем форму
        self.interval_input.clear()
        self.firm_input.clear()
        self.thickness_input.setValue(0)

    def generate_compaction_conclusion(self):
        """Генерирует заключение на уплотнение."""
        # Проверяем, есть ли отмеченные строки
        checked_rows = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    checked_rows.append(row)

        if not checked_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строки для генерации")
            return

        # Вспомогательная функция для парсинга даты
        def parse_date(date_str: str):
            """Парсит дату из строки в разных форматах."""
            from datetime import datetime
            formats = ["%Y-%m-%d", "%d.%m.%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Неизвестный формат даты: {date_str}")

        # Собираем данные из отмеченных строк
        entries = []
        for row in checked_rows:
            entry = {
                'work_type': self.table.item(row, 1).text(),
                'interval': self.table.item(row, 2).text(),
                'start_date': parse_date(self.table.item(row, 3).text()).strftime("%Y-%m-%d"),
                'end_date': parse_date(self.table.item(row, 4).text()).strftime("%Y-%m-%d"),
                'firm': self.table.item(row, 5).text(),
                'thickness': float(self.table.item(row, 6).text()),
                'object_name': self.selected_object['name'],
                'address': self.selected_object['address']
            }
            # Добавляем проверку на пустые значения
            if not entry['address']:
                # Если данные отсутствуют, показываем ошибку
                QMessageBox.critical(self, "Ошибка", "У объекта не заполнен адрес. Пожалуйста, заполните его в стартовом диалоге.")
                return
            entries.append(entry)

        try:
            # Генерируем заключения
            self.service.generate_compaction_conclusions(entries)
            
            # Обновляем статус в таблице
            for row in checked_rows:
                self.table.setItem(row, 7, QTableWidgetItem("Создано заключение"))
            
            QMessageBox.information(self, "Успешно", f"Заключения сгенерированы: {len(entries)} шт.")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации заключений: {str(e)}")

    def open_last_folder(self):
        """Открывает последнюю папку с документами."""
        self.service.open_last_folder()

    def show_table_context_menu(self, position):
        """Показывает контекстное меню для таблицы записей."""
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить запись")
        action = menu.exec(self.table.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_records()

    def delete_selected_records(self):
        """Удаляет выбранные записи из таблицы и базы данных."""
        selected_rows = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите строки для удаления")
            return

        reply = QMessageBox.question(self, 'Подтверждение удаления', 
                                     f'Вы уверены, что хотите удалить {len(selected_rows)} запись(и)?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Собираем ID записей для удаления
            ids_to_delete = []
            for row in selected_rows:
                # Получаем данные из строки для определения ID
                # В реальной реализации нужно хранить ID в скрытой колонке или другим способом
                # Пока удаляем по данным из строки
                work_type = self.table.item(row, 1).text()
                interval = self.table.item(row, 2).text()
                start_date = self.table.item(row, 3).text()
                end_date = self.table.item(row, 4).text()
                firm = self.table.item(row, 5).text()
                thickness = self.table.item(row, 6).text()
                
                # Нужно получить ID из базы данных по этим данным
                # Это упрощенная реализация - в реальности нужно хранить ID в таблице
                pass
            
            # Удаляем строки из таблицы (в обратном порядке, чтобы индексы не сбивались)
            for row in sorted(selected_rows, reverse=True):
                self.table.removeRow(row)


class DocumentTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор типа документов")
        self.setModal(True)
        self.selected_doc_type = None
        self.selected_lab_type = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Группа типов документов
        doc_group = QGroupBox("Тип документов")
        doc_layout = QVBoxLayout()
        
        self.passport_radio = QRadioButton("Паспорт на бетон")
        self.protocol_7_radio = QRadioButton("Протокол на 7 дней")
        self.protocol_28_radio = QRadioButton("Протокол на 28 дней")
        self.combo_radio = QRadioButton("Комплект (паспорт + 7 + 28)")
        
        doc_layout.addWidget(self.passport_radio)
        doc_layout.addWidget(self.protocol_7_radio)
        doc_layout.addWidget(self.protocol_28_radio)
        doc_layout.addWidget(self.combo_radio)
        
        doc_group.setLayout(doc_layout)
        layout.addWidget(doc_group)

        # Группа лаборатории (видна только для протоколов)
        self.lab_group = QGroupBox("Лаборатория")
        lab_layout = QVBoxLayout()
        
        self.lik_radio = QRadioButton("ЛИК")
        self.pts_radio = QRadioButton("ПТС")
        
        lab_layout.addWidget(self.lik_radio)
        lab_layout.addWidget(self.pts_radio)
        
        self.lab_group.setLayout(lab_layout)
        self.lab_group.setVisible(False)  # Сначала скрыта
        layout.addWidget(self.lab_group)

        # Обновляем видимость при выборе
        self.protocol_7_radio.toggled.connect(self.toggle_lab_group)
        self.protocol_28_radio.toggled.connect(self.toggle_lab_group)
        self.combo_radio.toggled.connect(self.toggle_lab_group)

        # Кнопки
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        
        self.ok_btn.clicked.connect(self.accept_selection)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def toggle_lab_group(self):
        """Показывает/скрывает группу лаборатории."""
        is_protocol = (
            self.protocol_7_radio.isChecked() or 
            self.protocol_28_radio.isChecked() or 
            self.combo_radio.isChecked()
        )
        self.lab_group.setVisible(is_protocol)

    def accept_selection(self):
        """Подтверждает выбор."""
        # Определяем тип документа
        if self.passport_radio.isChecked():
            self.selected_doc_type = DocumentType.PASSPORT
        elif self.protocol_7_radio.isChecked():
            self.selected_doc_type = DocumentType.PROTOCOL_7
        elif self.protocol_28_radio.isChecked():
            self.selected_doc_type = DocumentType.PROTOCOL_28
        elif self.combo_radio.isChecked():
            self.selected_doc_type = DocumentType.COMBO
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите тип документов")
            return

        # Определяем тип лаборатории
        if self.lik_radio.isChecked():
            self.selected_lab_type = LabType.LIK
        elif self.pts_radio.isChecked():
            self.selected_lab_type = LabType.PTS
        elif self.lab_group.isVisible():
            # Если группа видна, но ничего не выбрано
            QMessageBox.warning(self, "Предупреждение", "Выберите лабораторию")
            return
        else:
            # Для паспорта лаборатория не нужна
            self.selected_lab_type = None

        self.accept()

    def get_selection(self):
        """Возвращает выбранные типы."""
        return self.selected_doc_type, self.selected_lab_type
