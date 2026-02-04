#!/usr/bin/env python3
"""
Unit tests for core modules.
"""

from datetime import datetime
from core.numbering import excel_serial_date, generate_passport_number, generate_protocol_number, generate_conclusion_number
from core.calculations import (
    get_required_strength_28, get_required_strength_7, generate_density,
    generate_mass1, generate_mass2, generate_mass3, generate_strength_28,
    calculate_destroying_load, generate_compaction_data, calculate_average,
    calculate_compaction_coefficient
)


def test_excel_serial_date():
    date = datetime(2025, 2, 2)
    serial = excel_serial_date(date)
    print(f"Excel serial for 02.02.2025: {serial}")  # Should be around 45690
    assert serial > 45000, "Serial date seems incorrect"


def test_passport_number():
    date = datetime(2025, 2, 2)
    num = generate_passport_number(date, [])
    print(f"Passport number: {num}")
    assert num.startswith("17-0000"), "Invalid passport format"


def test_protocol_number():
    date = datetime(2025, 2, 2)
    num = generate_protocol_number(date, 7, [])
    print(f"Protocol 7 days: {num}")
    assert "-7/" in num, "Invalid protocol format"


def test_conclusion_number():
    date = datetime(2025, 2, 2)
    num = generate_conclusion_number(date, [])
    print(f"Conclusion number: {num}")
    assert "/" in num and len(num.split("/")[0].split(".")) == 3, "Invalid conclusion format"


def test_strength_calculations():
    grade = "В15"
    req_28 = get_required_strength_28(grade)
    req_7 = get_required_strength_7(grade)
    print(f"Required strength В15: 28d={req_28}, 7d={req_7}")
    assert req_28 == 19.25, "Incorrect required strength"
    assert req_7 == 13.47, "Incorrect 7d strength"


def test_density_mass():
    grade = "В15"
    density = generate_density(grade)
    mass1 = generate_mass1(density)
    mass2 = generate_mass2(mass1)
    mass3 = generate_mass3(mass2)
    print(f"Density: {density}, Masses: {mass1}, {mass2}, {mass3}")
    assert 2370 <= density <= 2380, "Density out of range"
    assert mass1 > 0, "Mass1 invalid"


def test_strength_load():
    grade = "В15"
    strength = generate_strength_28(grade)
    load = calculate_destroying_load(strength)
    print(f"Strength: {strength}, Load: {load}")
    assert 19 <= strength <= 20, "Strength out of range"


def test_compaction():
    data = generate_compaction_data(1)
    print(f"Compaction data keys: {list(data.keys())}")
    assert 'layer1_avg_coeff' in data, "Missing avg coeff"
    avg_coeff = data['layer1_avg_coeff']
    print(f"Average coeff: {avg_coeff}")
    assert 0.93 <= avg_coeff <= 0.99, "Coeff out of range"


if __name__ == "__main__":
    print("Testing core modules...")
    test_excel_serial_date()
    test_passport_number()
    test_protocol_number()
    test_conclusion_number()
    test_strength_calculations()
    test_density_mass()
    test_strength_load()
    test_compaction()
    print("All tests passed!")