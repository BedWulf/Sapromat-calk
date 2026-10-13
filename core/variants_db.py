"""
Модуль загрузки базы данных вариантов заданий из JSON-файла.

База разделена на две независимые части (как в методичке):
  * `schemes`   — схемы нагружения (Приложение 2): закрепление + нагрузки;
  * `data_sets` — числовые данные P, q, l, [σ], E (Приложение 1).
Плюс готовые комбинации в `variants` (номер варианта = схема + данные).

Такая структура позволяет в GUI выбрать схему и данные НЕЗАВИСИМО друг от
друга, а также полностью ручной режим ("Своя схема / свои данные").

Поддержка сборки в standalone .exe через PyInstaller:
при заморозке (sys.frozen) файл variants_db.json ищется внутри
архива во временной папке sys._MEIPASS (туда он кладётся директивой
datas=[('core/variants_db.json', 'core')] в build.spec).
При запуске из исходников — рядом с этим модулем.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional


@dataclass
class LoadEntry:
    """Одна нагрузка в схеме варианта.

    Attributes:
        segment: номер участка, 1..4 (как в методичке).
        load_type: "force" (сосредоточенная сила P) или "distributed" (нагрузка q).
        direction: 1 = вправо (по оси +z), -1 = влево (против оси +z).
        count: кратность нагрузки (1 -> P или q, 2 -> 2P или 2q и т.д.).
    """

    segment: int
    load_type: str          # "force" | "distributed"
    direction: int          # 1 = вправо (+z), -1 = влево (-z)
    count: int = 1          # кратность: 1 -> P/q, 2 -> 2P/2q ...


@dataclass
class NumericData:
    """Числовые данные варианта (строка таблицы Приложение 1)."""

    data_id: str            # "1", "2", ... или "" для ручного ввода
    P: float                # кН
    q: float                # кН/м
    l: float                # м (длина одного участка)
    sigma_allow: float      # МПа
    E: float                # МПа


@dataclass
class Scheme:
    """Схема нагружения (Приложение 2)."""

    scheme_id: str                  # "1", "2", ... или "" для своей схемы
    name: str                       # человекочитаемое название
    support_side: str               # "left" | "right" — место закрепления
    loads: List[LoadEntry] = field(default_factory=list)


@dataclass
class VariantData:
    """Полное описание варианта: схема + числовые данные.

    Сформирован либо из готовой записи `variants`, либо путём
    комбинирования Scheme и NumericData в GUI.
    """

    variant_id: str
    P: float
    q: float
    l: float
    sigma_allow: float
    E: float
    support_side: str
    loads: List[LoadEntry] = field(default_factory=list)
    scheme_id: str = ""
    data_id: str = ""

    @staticmethod
    def from_parts(scheme: Scheme, data: NumericData,
                   variant_id: Optional[str] = None) -> "VariantData":
        """Собрать вариант из независимых схемы и данных."""
        vid = variant_id if variant_id is not None else \
            f"{scheme.scheme_id}-{data.data_id}"
        return VariantData(
            variant_id=vid,
            P=data.P, q=data.q, l=data.l,
            sigma_allow=data.sigma_allow, E=data.E,
            support_side=scheme.support_side,
            loads=list(scheme.loads),
            scheme_id=scheme.scheme_id,
            data_id=data.data_id,
        )


@dataclass
class VariantsDB:
    """Вся база: готовые варианты + раздельные схемы и данные."""

    variants: List[VariantData]
    schemes: List[Scheme]
    data_sets: List[NumericData]

    def get_variant(self, variant_id: str) -> Optional[VariantData]:
        for v in self.variants:
            if v.variant_id == variant_id:
                return v
        return None

    def get_scheme(self, scheme_id: str) -> Optional[Scheme]:
        for s in self.schemes:
            if s.scheme_id == scheme_id:
                return s
        return None

    def get_data_set(self, data_id: str) -> Optional[NumericData]:
        for d in self.data_sets:
            if d.data_id == data_id:
                return d
        return None


def _get_resource_path(relative_path: str) -> str:
    """Вернуть абсолютный путь к ресурсу с учётом PyInstaller (_MEIPASS)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path: str = sys._MEIPASS  # type: ignore[attr-defined]
        return os.path.join(base_path, relative_path)

    module_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.basename(relative_path)
    candidate = os.path.join(module_dir, filename)
    if not os.path.isfile(candidate):
        candidate = os.path.join(os.path.dirname(module_dir), relative_path)
    return candidate


def _parse_load(raw: dict) -> LoadEntry:
    return LoadEntry(
        segment=int(raw["segment"]),
        load_type=str(raw["type"]),
        direction=int(raw["direction"]),
        count=int(raw.get("count", 1)),
    )


def _num_sort_key(value: str) -> tuple:
    """Ключ сортировки: сначала числа по возрастанию, затем прочие строки."""
    try:
        return (0, int(value), "")
    except (ValueError, TypeError):
        return (1, 0, str(value))


def load_database(json_path: Optional[str] = None) -> VariantsDB:
    """Загрузить полную базу (варианты + схемы + наборы данных).

    Args:
        json_path: необязательный явный путь к variants_db.json.

    Returns:
        Объект VariantsDB.

    Raises:
        FileNotFoundError: если файл базы не найден.
        ValueError: при некорректной структуре данных в файле.
    """
    path: str = json_path or _get_resource_path(os.path.join("core", "variants_db.json"))

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Файл базы вариантов не найден: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError("Ожидался JSON-объект верхнего уровня.")

    # ---------------- Числовые данные ----------------
    data_sets: List[NumericData] = []
    for rec in raw.get("data_sets", []):
        data_sets.append(NumericData(
            data_id=str(rec.get("id", "")),
            P=float(rec["P"]),
            q=float(rec["q"]),
            l=float(rec["l"]),
            sigma_allow=float(rec["sigma_allow"]),
            E=float(rec["E"]),
        ))

    # ---------------- Схемы нагружения ----------------
    schemes: List[Scheme] = []
    for rec in raw.get("schemes", []):
        schemes.append(Scheme(
            scheme_id=str(rec.get("scheme_id", "")),
            name=str(rec.get("name", f"Схема {rec.get('scheme_id', '?')}")),
            support_side=str(rec.get("support_side", "right")),
            loads=[_parse_load(ld) for ld in rec.get("loads", [])],
        ))

    # ---------------- Готовые варианты ----------------
    records = raw.get("variants", [])
    if not isinstance(records, list):
        raise ValueError("Ожидался список вариантов по ключу 'variants'.")

    variants: List[VariantData] = []
    for rec in records:
        scheme_no = str(rec.get("scheme_number", ""))
        data_no = str(rec.get("data_number", ""))
        scheme = next((s for s in schemes if s.scheme_id == scheme_no), None)
        data = next((d for d in data_sets if d.data_id == data_no), None)

        if scheme is not None and data is not None:
            # Канонический способ: собираем из частей (единый источник истины)
            var = VariantData.from_parts(scheme, data, variant_id=str(rec["variant_id"]))
        else:
            # Совместимость со старым форматом: всё записано прямо в варианте
            var = VariantData(
                variant_id=str(rec["variant_id"]),
                P=float(rec["P"]),
                q=float(rec["q"]),
                l=float(rec["l"]),
                sigma_allow=float(rec["sigma_allow"]),
                E=float(rec["E"]),
                support_side=str(rec.get("support_side", "right")),
                loads=[_parse_load(ld) for ld in rec.get("loads", [])],
                scheme_id=scheme_no,
                data_id=data_no,
            )
        variants.append(var)

    variants.sort(key=lambda v: _num_sort_key(v.variant_id))
    schemes.sort(key=lambda s: _num_sort_key(s.scheme_id))
    data_sets.sort(key=lambda d: _num_sort_key(d.data_id))

    return VariantsDB(variants=variants, schemes=schemes, data_sets=data_sets)


def load_variants(json_path: Optional[str] = None) -> List[VariantData]:
    """Обратно совместимый API: только список готовых вариантов."""
    return load_database(json_path).variants
