"""
Главное окно приложения.
"""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget
)

from gui.tab_beton import TabBeton
from gui.tab_compaction import TabCompaction


class MainWindow(QMainWindow):
    def __init__(self, db, selected_object):
        super().__init__()
        self.db = db
        self.selected_object = selected_object
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Генератор документов - {self.selected_object['name']}")
        self.setGeometry(100, 100, 1000, 700)
        
        # Создаем вкладки
        self.tabs = QTabWidget()
        
        # Вкладка "Бетон"
        self.tab_beton = TabBeton(self.db, self.selected_object)
        self.tabs.addTab(self.tab_beton, "Бетон")
        
        # Вкладка "Уплотнение"
        self.tab_compaction = TabCompaction(self.db, self.selected_object)
        self.tabs.addTab(self.tab_compaction, "Уплотнение")
        
        self.setCentralWidget(self.tabs)
