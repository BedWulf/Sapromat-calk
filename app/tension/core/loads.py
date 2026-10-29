from dataclasses import dataclass
from enum import Enum

class Direction(Enum):
    POSITIVE = 1   # По оси +z (вправо)
    NEGATIVE = -1  # Против оси +z (влево)

@dataclass
class Load:
    """Базовый класс нагрузки"""
    start: float          # координата начала приложения [м]
    direction: Direction  # направление

@dataclass
class ConcentratedForce(Load):
    """Сосредоточенная сила P [кН]"""
    magnitude: float = 0.0  # кН

@dataclass
class DistributedLoad(Load):
    """Распределённая нагрузка q [кН/м] от start до end"""
    intensity: float = 0.0  # кН/м
    end: float = 0.0        # м