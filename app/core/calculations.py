"""
Модуль расчетов для всех формул, эквивалентных Excel.
"""

import random
from typing import Dict, List, Tuple, Union
from dataclasses import dataclass

def to_float(val: Union[str, float, int, None]) -> float:
    """Преобразует значение в float, корректно обрабатывая строки с запятой."""
    if val is None:
        return 0.0
    if isinstance(val, str):
        val = val.replace(',', '.').strip()
    return float(val)


@dataclass
class ConcreteGrade:
    name: str
    strength_28_min: float
    strength_28_max: float
    density_min: int
    density_max: int
    required_strength_28: float
    required_strength_7: float


CONCRETE_GRADES: Dict[str, ConcreteGrade] = {
    "В7,5": ConcreteGrade("В7,5", 9.61, 9.72, 2335, 2345, 9.62, 6.73),
    "В15": ConcreteGrade("В15", 19.25, 19.35, 2370, 2380, 19.25, 13.47),
    "В20": ConcreteGrade("В20", 25.7, 25.77, 2390, 2400, 25.67, 17.97),
    "В22,5": ConcreteGrade("В22,5", 28.85, 29.0, 2405, 2415, 28.9, 20.23),
    "В25": ConcreteGrade("В25", 32.1, 32.2, 2415, 2425, 32.1, 22.47),
    "В30": ConcreteGrade("В30", 38.29, 38.44, 2425, 2435, 38.34, 26.84),
    "В35": ConcreteGrade("В35", 44.95, 45.02, 2465, 2475, 44.92, 31.44),
    "В40": ConcreteGrade("В40", 51.35, 51.45, 2505, 2515, 51.35, 35.95),
    "В50": ConcreteGrade("В50", 64.21, 64.3, 2565, 2575, 64.2, 44.94),
}


@dataclass
class MortarGrade:
    name: str
    strength_28_min: float
    strength_28_max: float
    density_min: int
    density_max: int
    required_strength_28: float
    required_strength_7: float


MORTAR_GRADES: Dict[str, MortarGrade] = {
    "Раствор М100": MortarGrade("Раствор М100", 12.0, 13.0, 1800, 1900, 12.5, 8.75),
    "Раствор М150": MortarGrade("Раствор М150", 18.0, 19.0, 1850, 1950, 18.75, 13.13),
    "Раствор М200": MortarGrade("Раствор М200", 24.0, 25.0, 1900, 2000, 25.0, 17.5),
}


# Mapping of grades to their full names
GRADE_FULL_NAMES = {
    "В7,5": "БСТ В7,5  П4 F50  W2",
    "В15": "БСТ В15   П4 F100 W4",
    "В20": "БСТ В20   П4 F150 W6",
    "В22,5": "БСТ В22,5 П4 F150 W6",
    "В25": "БСТ В25   П4 F200 W8",
    "В30": "БСТ В30   П4 F300 W10",
    "В35": "БСТ В35   П4 F300 W10",
    "В40": "БСТ В40   П4 F400 W12",
    "В50": "БСТ В50   П4 F500 W14",
    "Раствор М100": "Раствор строительный М100Пк3F50",
    "Раствор М150": "Раствор строительный М150Пк3F50",
    "Раствор М200": "Раствор строительный М200Пк3F50"
}


def get_grade_full_name(grade: str) -> str:
    """Get full name for concrete grade."""
    return GRADE_FULL_NAMES.get(grade, grade)


def get_required_strength_28(grade: str) -> float:
    """Получает требуемую прочность на 28 сутки."""
    if grade.startswith("Раствор"):
        # Для раствора используем требуемую прочность бетона В7,5
        return CONCRETE_GRADES.get("В7,5").required_strength_28
    return CONCRETE_GRADES.get(grade, CONCRETE_GRADES["В7,5"]).required_strength_28


def get_required_strength_7(grade: str) -> float:
    """Получает требуемую прочность на 7 сутки (70% от 28)."""
    return round(get_required_strength_28(grade) * 0.7, 2)


def generate_density(grade: str) -> int:
    """Генерирует среднюю плотность для марки бетона или раствора."""
    if grade.startswith("Раствор"):
        g = MORTAR_GRADES.get(grade, MORTAR_GRADES["Раствор М100"])
    else:
        g = CONCRETE_GRADES.get(grade, CONCRETE_GRADES["В7,5"])
    return random.randint(g.density_min, g.density_max)


def generate_mass1(density: int) -> float:
    """Генерирует массу1: round(0.001 * density * 1000, 2)"""
    return round(0.001 * density * 1000, 2)


def generate_mass2(mass1: float) -> int:
    """Генерирует массу2: round(random между mass1-5 и mass1+5, 0)"""
    return round(random.uniform(mass1 - 5, mass1 + 5), 0)


def generate_mass3(mass2: float) -> int:
    """Генерирует массу3: round(random между mass2+2 и mass2-3, 0)"""
    return round(random.uniform(mass2 + 2, mass2 - 3), 0)


def generate_strength_28(grade: str) -> float:
    """Генерирует фактическую прочность на 28 сутки для бетона или раствора."""
    if grade.startswith("Раствор"):
        # Для раствора используем параметры бетона В7,5
        g = CONCRETE_GRADES.get("В7,5")
    else:
        g = CONCRETE_GRADES.get(grade, CONCRETE_GRADES["В7,5"])
    return random.uniform(g.strength_28_min, g.strength_28_max)


def generate_strength_variation(strength_28: float) -> float:
    """Генерирует вариацию для второго/третьего образца."""
    return round(random.uniform(strength_28 - 0.08, strength_28 + 0.1), 2)


def calculate_destroying_load(strength_28: float) -> int:
    """Рассчитывает разрушающую нагрузку: round(strength_28 / 0.9111 * 10, 0)"""
    return round(strength_28 / 0.9111 * 10, 0)


def generate_destroying_load_variation(base_load: int) -> int:
    """Генерирует вариацию для разрушающей нагрузки."""
    return round(random.uniform(base_load - 5, base_load + 5), 0)


def calculate_destroying_load_7days(strength_28: float) -> int:
    """Рассчитывает разрушающую нагрузку для 7-дневных протоколов с округлением на 0.8"""
    destroying_load = round(strength_28 / 0.9111 * 10, 0)
    # Для 7-дневных протоколов применяем округление на 0.8
    return round(destroying_load * 0.8, 0)


def calculate_strength_from_load(load: int, age_coeff: float = 1.0) -> float:
    """Рассчитывает прочность по нагрузке: round((load / 10 * 0.9111) * age_coeff, 2)"""
    return round((load / 10 * 0.9111) * age_coeff, 2)


def generate_compaction_measurements() -> List[int]:
    """Генерирует 18 случайных измерений (23-29) для уплотнения."""
    return [random.randint(23, 29) for _ in range(18)]


def calculate_average(measurements: List[float]) -> float:
    """Рассчитывает среднее значение измерений."""
    return sum(measurements) / len(measurements)


def calculate_compaction_coefficient(average_measurement: float) -> float:
    """Рассчитывает коэффициент уплотнения по среднему измерению."""
    mapping = {
        23: 0.93, 24: 0.94, 25: 0.95, 26: 0.96,
        27: 0.97, 28: 0.98, 29: 0.99
    }
    # Округляем до ближайшего целого для отображения
    key = round(average_measurement)
    return mapping.get(key, 0.95)  # По умолчанию 0.95


def generate_compaction_data(num_layers: int) -> Dict[str, List[float]]:
    """Генерирует данные для заключения по уплотнению с num_layers (1 или 3)."""
    measurements = generate_compaction_measurements()  # 18 измерений
    data = {}
    for layer in range(1, num_layers + 1):
        layer_measurements = measurements[(layer-1)*18//num_layers:layer*18//num_layers]  # Делим поровну
        averages = []
        coeffs = []
        for i in range(6):
            start = i * 3
            end = (i + 1) * 3
            avg = calculate_average(layer_measurements[start:end])
            averages.append(avg)
            coeffs.append(calculate_compaction_coefficient(avg))
        data[f'layer{layer}_averages'] = averages
        data[f'layer{layer}_coeffs'] = coeffs
        data[f'layer{layer}_avg_coeff'] = calculate_average(coeffs)
    return data
