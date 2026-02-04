"""
Модуль DOCX Engine для генерации документов из шаблонов.
"""

from pathlib import Path
from typing import Dict, Optional
from docx import Document


class DocxGenerator:
    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.doc: Optional[Document] = None

    def load_template(self):
        """Загружает DOCX шаблон."""
        self.doc = Document(self.template_path)

    def replace_placeholders(self, data: Dict[str, str]):
        """Replace {key} placeholders with values from data dict."""
        if not self.doc:
            raise ValueError("Template not loaded")

        # Replace in paragraphs
        for paragraph in self.doc.paragraphs:
            self._replace_in_paragraph(paragraph, data)

        # Replace in tables
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._replace_in_paragraph(paragraph, data)

        # Replace in headers and footers
        for section in self.doc.sections:
            for header in [section.header, section.footer]:
                if header is not None:
                    for paragraph in header.paragraphs:
                        self._replace_in_paragraph(paragraph, data)
                    for table in header.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                for paragraph in cell.paragraphs:
                                    self._replace_in_paragraph(paragraph, data)

    def _replace_in_paragraph(self, paragraph, data: Dict[str, str]):
        """Заменяет плейсхолдеры в одном абзаце."""
        # Объединяем весь текст параграфа для поиска плейсхолдеров
        full_text = ''.join(run.text for run in paragraph.runs)
        
        # Для отладки - выводим, какие плейсхолдеры ищем и что нашли
        placeholders_found = []
        for key in data.keys():
            placeholder = f"{{{key}}}"
            if placeholder in full_text:
                placeholders_found.append(placeholder)
        
        if placeholders_found:
            # Выполняем замены в объединенном тексте
            modified_text = full_text
            for key, value in data.items():
                placeholder = f"{{{key}}}"
                modified_text = modified_text.replace(placeholder, str(value))
            
            # Разбиваем модифицированный текст обратно на раны
            # Очищаем существующие раны
            for i in range(1, len(paragraph.runs)):
                paragraph.runs[i].text = ""
            
            # Обновляем первый ран с новым содержимым
            if paragraph.runs:
                paragraph.runs[0].text = modified_text

    def remove_table_rows_after_marker(self, marker: str):
        """Удаляет все строки таблицы после строки, содержащей {marker}."""
        if not self.doc:
            raise ValueError("Шаблон не загружен")

        for table in self.doc.tables:
            marker_row_index = None
            for i, row in enumerate(table.rows):
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if f"{{{marker}}}" in paragraph.text:
                            marker_row_index = i
                            break
                    if marker_row_index is not None:
                        break
                if marker_row_index is not None:
                    break

            if marker_row_index is not None:
                # Удаляем строки после маркера
                rows_to_remove = len(table.rows) - marker_row_index - 1
                for _ in range(rows_to_remove):
                    table._tbl.remove(table.rows[-1]._tr)
                break  # Предполагаем один маркер на документ

    def save_document(self, output_path: Path):
        """Сохраняет измененный документ."""
        if not self.doc:
            raise ValueError("Шаблон не загружен")
        # Создаем директорию, если она не существует
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(output_path)


def generate_document(template_path: Path, data: Dict[str, str], output_path: Path, num_layers: int = 1):
    """
    Генерирует DOCX документ из шаблона с заменой плейсхолдеров.
    Для заключений по уплотнению удаляет лишние слои при num_layers < 3.
    """
    generator = DocxGenerator(template_path)
    generator.load_template()
    generator.replace_placeholders(data)

    # Для шаблонов уплотнения удаляем лишние слои
    if "наим_слой2" in data and num_layers == 1:
        generator.remove_table_rows_after_marker("наим_слой2")
    elif "наим_слой3" in data and num_layers == 2:
        generator.remove_table_rows_after_marker("наим_слой3")

    generator.save_document(output_path)
