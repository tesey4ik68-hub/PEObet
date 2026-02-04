#!/usr/bin/env python3
"""
Точка входа в приложение.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from core.database import DatabaseManager
from gui.start_dialog import StartDialog
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # Инициализация БД
    db = DatabaseManager()
    
    # Показываем стартовый диалог
    start_dialog = StartDialog(db)
    if start_dialog.exec() == StartDialog.Accepted:
        selected_object = start_dialog.selected_object
        
        # Открываем главное окно
        main_window = MainWindow(db, selected_object)
        main_window.show()
        
        sys.exit(app.exec())


if __name__ == "__main__":
    main()