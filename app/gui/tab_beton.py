"""
Вкладка "Бетон".
"""

from datetime import datetime
from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QPushButton, QTableWidgetItem,
    QHeaderView, QMessageBox, QLabel, QDateEdit, QCheckBox, QGroupBox,
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup, QRadioButton,
    QTableWidget, QMenu, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from core.services.document_service import DocumentService, DocumentType, LabType


class TabBeton(QWidget):
    def __init__(self, db, selected_object):
        super().__init__()
        self.db = db
        self.selected_object = selected_object
        self.service = DocumentService(db)
        self.init_ui()
        
        # Загружаем существующие записи для объекта
        self.load_existing_entries()
    
    def load_existing_entries(self):
        """Загружает существующие записи для объекта из базы данных."""
        entries = self.db.get_concrete_entries(self.selected_object['name'])
        for entry in entries:
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
            
            # Данные из базы
            pour_date = datetime.strptime(entry['pour_date'], "%Y-%m-%d").date()
            self.table.setItem(row, 1, QTableWidgetItem(entry['grade']))
            self.table.setItem(row, 2, QTableWidgetItem(str(entry['volume'])))
            self.table.setItem(row, 3, QTableWidgetItem(pour_date.strftime("%d.%m.%Y")))
            self.table.setItem(row, 4, QTableWidgetItem(entry['network'] if entry['network'] else ''))
            self.table.setItem(row, 5, QTableWidgetItem(entry['area']))
            self.table.setItem(row, 6, QTableWidgetItem(entry['status']))

    def init_ui(self):
        layout = QVBoxLayout()

        # Форма ввода
        form_group = QGroupBox("Добавить запись")
        form_layout = QFormLayout()
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["В7,5", "В15", "В20", "В22,5", "В25", "В30", "В35", "В40", "В50", 
                                   "Раствор М100", "Раствор М150", "Раствор М200"])
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0, 99999)
        self.pour_date_input = QDateEdit()
        self.pour_date_input.setDate(QDate.currentDate())
        self.pour_date_input.setCalendarPopup(True)
        self.network_input = QLineEdit()
        self.area_input = QLineEdit()  # Новое поле "Участок"

        form_layout.addRow("Марка:", self.grade_combo)
        form_layout.addRow("Объем:", self.volume_input)
        form_layout.addRow("Дата заливки:", self.pour_date_input)
        form_layout.addRow("Сеть:", self.network_input)
        form_layout.addRow("Участок:", self.area_input)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Кнопки под формой
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить в таблицу")
        self.add_btn.setStyleSheet("background-color: blue; color: white;")
        self.generate_btn = QPushButton("Сформировать документы")
        self.generate_btn.setStyleSheet("background-color: green; color: white;")
        self.open_folder_btn = QPushButton("Открыть папку с документами")
        self.open_folder_btn.setStyleSheet("background-color: lightblue; color: black;")
        
        self.add_btn.clicked.connect(self.add_to_table)
        self.generate_btn.clicked.connect(self.generate_documents)
        self.open_folder_btn.clicked.connect(self.open_last_folder)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.open_folder_btn)
        
        layout.addLayout(button_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # Чекбокс + 6 полей
        self.table.setHorizontalHeaderLabels(["", "Марка", "Объем", "Дата заливки", "Сеть", "Участок", "Статус"])
        
        # Устанавливаем ширину первого столбца для чекбоксов
        self.table.setColumnWidth(0, 30)
        # Устанавливаем ширину столбца "Марка" до 100 пикселей
        self.table.setColumnWidth(1, 100)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)

        layout.addWidget(self.table)

        # Протоколы
        self.protocol_table = QTableWidget()
        self.protocol_table.setColumnCount(7)
        self.protocol_table.setHorizontalHeaderLabels(['Номер', 'Марка', 'Треб. прочность', 'Участок', 'Фирма', 'Объект', 'Дата'])
        self.protocol_table.horizontalHeader().setStretchLastSection(True)
        self.protocol_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.protocol_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.protocol_table.verticalHeader().setVisible(False)
        self.protocol_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.protocol_table.customContextMenuRequested.connect(self.show_protocol_context_menu)

        layout.addWidget(self.protocol_table)

        self.setLayout(layout)

    def add_to_table(self):
        """Добавляет запись в таблицу."""
        grade = self.grade_combo.currentText()
        volume = self.volume_input.value()
        pour_date = self.pour_date_input.date().toPython()
        network = self.network_input.text().strip()
        area = self.area_input.text().strip()

        if not area:
            QMessageBox.warning(self, "Предупреждение", "Введите участок")
            return

        # Подготовка данных для сохранения
        data = {
            'object_name': self.selected_object['name'],
            'grade': grade,
            'volume': volume,
            'pour_date': pour_date.strftime("%Y-%m-%d"),
            'network': network,
            'area': area,
            'status': 'Ожидает'
        }

        # Сохраняем в базу данных
        entry_id = self.db.save_concrete_entry(data)

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
        self.table.setItem(row, 1, QTableWidgetItem(grade))
        self.table.setItem(row, 2, QTableWidgetItem(str(volume)))
        self.table.setItem(row, 3, QTableWidgetItem(pour_date.strftime("%d.%m.%Y")))
        self.table.setItem(row, 4, QTableWidgetItem(network))
        self.table.setItem(row, 5, QTableWidgetItem(area))
        self.table.setItem(row, 6, QTableWidgetItem("Ожидает"))

        # Очищаем форму
        self.volume_input.setValue(0)
        self.network_input.clear()
        self.area_input.clear()

    def generate_documents(self):
        """Генерирует документы."""
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

        # Диалог выбора типа документа
        dialog = DocumentTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            doc_type, lab_type = dialog.get_selection()
            
            # Собираем данные из отмеченных строк
            entries = []
            for row in checked_rows:
                entry = {
                    'grade': self.table.item(row, 1).text(),
                    'volume': float(self.table.item(row, 2).text()),
                    'pour_date': parse_date(self.table.item(row, 3).text()).strftime("%Y-%m-%d"),  # Конвертируем в стандартный формат
                    'network': self.table.item(row, 4).text(),
                    'area': self.table.item(row, 5).text(),  # участок
                    'object_name': self.selected_object['name'],
                    'address': self.selected_object['address'],
                    'firm': self.selected_object['firm']
                }
                # Добавляем проверку на пустые значения
                if not entry['address'] or not entry['firm']:
                    # Если данные отсутствуют, показываем ошибку
                    QMessageBox.critical(self, "Ошибка", "У объекта не заполнены фирма или адрес. Пожалуйста, заполните их в стартовом диалоге.")
                    return
                entries.append(entry)
            try:
                # Генерируем документы
                self.service.generate_documents(entries, doc_type, lab_type)
                
                # Обновляем статус в таблице
                status_text = {
                    DocumentType.PASSPORT: "Создан паспорт",
                    DocumentType.PROTOCOL_7: "Создан протокол 7 дней",
                    DocumentType.PROTOCOL_28: "Создан протокол 28 дней",
                    DocumentType.COMBO: "Создан комплект"
                }.get(doc_type, "Создан документ")
                
                for row in checked_rows:
                    self.table.setItem(row, 6, QTableWidgetItem(status_text))
                
                QMessageBox.information(self, "Успешно", f"Документы сгенерированы: {len(entries)} шт.")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации документов: {str(e)}")

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
                grade = self.table.item(row, 1).text()
                volume = float(self.table.item(row, 2).text())
                pour_date = self.table.item(row, 3).text()
                network = self.table.item(row, 4).text()
                area = self.table.item(row, 5).text()
                
                # Нужно получить ID из базы данных по этим данным
                # Это упрощенная реализация - в реальности нужно хранить ID в таблице
                pass
            
            # Удаляем строки из таблицы (в обратном порядке, чтобы индексы не сбивались)
            for row in sorted(selected_rows, reverse=True):
                self.table.removeRow(row)

    def show_protocol_context_menu(self, position):
        """Показывает контекстное меню для таблицы протоколов."""
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить протокол")
        action = menu.exec(self.protocol_table.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_protocols()

    def delete_selected_protocols(self):
        """Удаляет выбранные протоколы из таблицы и базы данных."""
        selected_rows = []
        for row in range(self.protocol_table.rowCount()):
            item = self.protocol_table.item(row, 0)  # Предполагаем, что первый столбец - это номер
            if item and item.isSelected():
                selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите протоколы для удаления")
            return

        reply = QMessageBox.question(self, 'Подтверждение удаления', 
                                     f'Вы уверены, что хотите удалить {len(selected_rows)} протокол(ы)?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Собираем номера протоколов для удаления
            numbers_to_delete = []
            for row in selected_rows:
                number = self.protocol_table.item(row, 0).text()
                numbers_to_delete.append(number)
            
            try:
                # Удаляем из базы данных
                self.db.delete_records("protocols", numbers_to_delete)
                
                # Удаляем строки из таблицы (в обратном порядке)
                for row in sorted(selected_rows, reverse=True):
                    self.protocol_table.removeRow(row)
                
                QMessageBox.information(self, "Успешно", f"Протоколы удалены: {len(numbers_to_delete)} шт.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении протоколов: {str(e)}")


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