"""
Стартовый диалог выбора объекта.
"""

import sqlite3
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QListWidget, QLabel, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt

from core.database import DatabaseManager


class StartDialog(QDialog):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.selected_object = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Выбор объекта")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Генератор документов для строительства")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Описание
        desc_label = QLabel(
            "Программа для генерации паспортов, протоколов и заключений\n"
            "на основе шаблонов документов"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Разделитель
        layout.addWidget(QLabel(""))
        
        # Группа выбора объекта
        select_group = QGroupBox("Выбрать существующий объект")
        select_layout = QVBoxLayout()
        
        self.objects_list = QListWidget()
        self.load_objects()
        select_layout.addWidget(self.objects_list)
        
        # Контекстное меню для обновления, удаления и редактирования
        self.objects_list.setContextMenuPolicy(Qt.ActionsContextMenu)
        refresh_action = self.objects_list.addAction("Обновить список")
        edit_action = self.objects_list.addAction("Редактировать объект")
        delete_action = self.objects_list.addAction("Удалить объект")
        
        refresh_action.triggered.connect(self.load_objects)
        delete_action.triggered.connect(self.delete_selected_object)
        edit_action.triggered.connect(self.edit_selected_object)
        
        select_group.setLayout(select_layout)
        layout.addWidget(select_group)
        
        # Группа создания нового объекта
        create_group = QGroupBox("Создать новый объект")
        create_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.firm_input = QLineEdit()
        
        create_layout.addRow("Наименование:", self.name_input)
        create_layout.addRow("Адрес:", self.address_input)
        create_layout.addRow("Фирма:", self.firm_input)
        
        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("Выбрать объект")
        self.create_btn = QPushButton("Создать объект")
        self.cancel_btn = QPushButton("Отмена")
        
        self.select_btn.clicked.connect(self.select_object)
        self.create_btn.clicked.connect(self.create_object)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def delete_selected_object(self):
        """Удаляет выбранный объект и все его записи."""
        selected_items = self.objects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите объект для удаления")
            return

        object_name = selected_items[0].text()
        reply = QMessageBox.question(
            self, "Подтверждение", 
            f"Вы уверены, что хотите удалить объект '{object_name}' и все его данные?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Удаляем объект и все его записи из базы данных
            self.db.delete_object_and_entries(object_name)
            # Обновляем список
            self.load_objects()

    def load_objects(self):
        """Загружает список существующих объектов."""
        try:
            self.objects_list.clear()
            # Получаем объекты из таблицы objects
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM objects ORDER BY name")
                rows = cursor.fetchall()
                for row in rows:
                    self.objects_list.addItem(row[0])
        except Exception as e:
            # Если таблица еще не создана, просто не загружаем объекты
            print(f"Ошибка загрузки объектов: {e}")

    def select_object(self):
        """Выбирает существующий объект."""
        selected_items = self.objects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите объект из списка")
            return
        
        object_name = selected_items[0].text()
        # Получаем данные объекта из базы данных
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, address, firm FROM objects WHERE name = ?", (object_name,))
                row = cursor.fetchone()
                if row:
                    self.selected_object = {
                        'name': row[0],
                        'address': row[1] if row[1] else '',
                        'firm': row[2] if row[2] else ''
                    }
                else:
                    # Если объект не найден, создаем его с пустыми значениями
                    self.selected_object = {
                        'name': object_name,
                        'address': '',
                        'firm': ''
                    }
        except Exception as e:
            print(f"Ошибка получения данных объекта: {e}")
            self.selected_object = {
                'name': object_name,
                'address': '',
                'firm': ''
            }
        self.accept()

    def create_object(self):
        """Создает новый объект."""
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        firm = self.firm_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Предупреждение", "Введите наименование объекта")
            return
        
        # Сохраняем объект в базу данных
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO objects (name, address, firm)
                VALUES (?, ?, ?)
            """, (name, address, firm))
            conn.commit()
        
        self.selected_object = {
            'name': name,
            'address': address,
            'firm': firm
        }
        self.accept()
    
    def edit_selected_object(self):
        """Редактирует выбранный объект."""
        selected_items = self.objects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите объект для редактирования")
            return

        object_name = selected_items[0].text()
        
        # Получаем текущие данные объекта
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, address, firm FROM objects WHERE name = ?", (object_name,))
                row = cursor.fetchone()
                if row:
                    current_address = row[1] if row[1] else ''
                    current_firm = row[2] if row[2] else ''
                else:
                    current_address = ''
                    current_firm = ''
        except Exception as e:
            print(f"Ошибка получения данных объекта для редактирования: {e}")
            current_address = ''
            current_firm = ''
        
        # Создаем диалог редактирования
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QLabel
        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle("Редактировать объект")
        edit_dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Редактирование объекта:"))
        
        name_edit = QLineEdit(object_name)
        address_edit = QLineEdit(current_address)
        firm_edit = QLineEdit(current_firm)
        
        form_layout = QFormLayout()
        form_layout.addRow("Наименование:", name_edit)
        form_layout.addRow("Адрес:", address_edit)
        form_layout.addRow("Фирма:", firm_edit)
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(edit_dialog.accept)
        button_box.rejected.connect(edit_dialog.reject)
        layout.addWidget(button_box)
        
        edit_dialog.setLayout(layout)
        
        if edit_dialog.exec() == QDialog.Accepted:
            new_name = name_edit.text().strip()
            new_address = address_edit.text().strip()
            new_firm = firm_edit.text().strip()
            
            if not new_name:
                QMessageBox.warning(self, "Предупреждение", "Введите наименование объекта")
                return
            
            # Обновляем объект в базе данных
            try:
                with sqlite3.connect(self.db.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE objects 
                        SET name = ?, address = ?, firm = ?
                        WHERE name = ?
                    """, (new_name, new_address, new_firm, object_name))
                    conn.commit()
                
                # Если имя объекта изменилось, обновляем записи в других таблицах
                if new_name != object_name:
                    # Обновляем записи в concrete_entries
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE concrete_entries 
                            SET object_name = ?
                            WHERE object_name = ?
                        """, (new_name, object_name))
                        conn.commit()
                
                # Обновляем список объектов
                self.load_objects()
                QMessageBox.information(self, "Успех", "Объект успешно обновлен")
            except Exception as e:
                print(f"Ошибка обновления объекта: {e}")
                QMessageBox.critical(self, "Ошибка", "Не удалось обновить объект")
