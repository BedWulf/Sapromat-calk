"""
Модуль загрузки базы данных вариантов заданий из JSON-файла.

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
from dataclasses import dataclass, field
from typing import List, Optional


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
class VariantData:
    """Полное описание одного варианта задания."""

    variant_id: str
    P: float                    # кН
    q: float                    # кН/м
    l: float                    # м (длина одного участка)
    sigma_allow: float          # МПа
    E: float                    # МПа
    support_side: str           # "left" | "right" — место закрепления стержня
    loads: List[LoadEntry] = field(default_factory=list)


def _get_resource_path(relative_path: str) -> str:
    """Вернуть абсолютный путь к ресурсу с учётом PyInstaller (_MEIPASS).

    Args:
        relative_path: путь относительно корня проекта, например
                       "core/variants_db.json".

    Returns:
        Абсолютный путь к файлу внутри собранного .exe (_MEIPASS) или
        рядом с исходным модулем при запуске из исходников.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # В собранном .exe: datas=[('core/variants_db.json', 'core')]
        # кладёт файл в <_MEIPASS>/core/variants_db.json
        base_path: str = sys._MEIPASS  # type: ignore[attr-defined]
        return os.path.join(base_path, relative_path)

    # В исходниках: core/variants_db.json рядом с этим модулем
    module_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.basename(relative_path)
    candidate = os.path.join(module_dir, filename)
    if not os.path.isfile(candidate):
        candidate = os.path.join(os.path.dirname(module_dir), relative_path)
    return candidate


def load_variants(json_path: Optional[str] = None) -> List[VariantData]:
    """Загрузить и распарсить все варианты из JSON-файла.

    Args:
        json_path: необязательный явный путь к variants_db.json.
                   По умолчанию — core/variants_db.json (с учётом _MEIPASS).

    Returns:
        Список VariantData, отсортированный по числовому id варианта.

    Raises:
        FileNotFoundError: если файл вариантов не найден.
        ValueError: при некорректной структуре данных в файле.
    """
    path: str = json_path or _get_resource_path(os.path.join("core", "variants_db.json"))

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Файл базы вариантов не найден: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    records = raw["variants"] if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        raise ValueError("Ожидался список вариантов по ключу 'variants'.")

    variants: List[VariantData] = []
    for rec in records:
        loads = [
            LoadEntry(
                segment=int(ld["segment"]),
                load_type=str(ld["type"]),
                direction=int(ld["direction"]),
                count=int(ld.get("count", 1)),
            )
            for ld in rec.get("loads", [])
        ]
        variants.append(
            VariantData(
                variant_id=str(rec["variant_id"]),
                P=float(rec["P"]),
                q=float(rec["q"]),
                l=float(rec["l"]),
                sigma_allow=float(rec["sigma_allow"]),
                E=float(rec["E"]),
                support_side=str(rec.get("support_side", "right")),
                loads=loads,
            )
        )

    def _sort_key(v: VariantData) -> tuple:
        try:
            return (0, int(v.variant_id), "")
        except ValueError:
            return (1, 0, v.variant_id)

    variants.sort(key=_sort_key)
    return variants
