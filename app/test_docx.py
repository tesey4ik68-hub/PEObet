#!/usr/bin/env python3
"""
Test DOCX engine.
"""

from pathlib import Path
from core.docx_engine import DocxGenerator

# Create a simple test template (manually create a docx with placeholders)
# For now, assume templates are copied

def test_replace():
    # Assuming template exists
    template_path = Path("templates/Шаблон бетон.docx")
    if not template_path.exists():
        print("Template not found, skipping test")
        return

    data = {
        "Нпаспорта": "17-000045690",
        "фирма": "ООО Тест",
        "марка": "В15"
    }

    generator = DocxGenerator(template_path)
    generator.load_template()
    generator.replace_placeholders(data)

    output_path = Path("test_output.docx")
    generator.save_document(output_path)

    print(f"Test document saved to {output_path}")

if __name__ == "__main__":
    test_replace()