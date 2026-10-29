import numpy as np

def macaulay(x: float, n: int) -> float:
    """Скобка Маколея: <x>^n = x^n при x>=0, иначе 0"""
    return x**n if x >= 0 else 0.0

def macaulay_array(x: np.ndarray, n: int) -> np.ndarray:
    """Векторизованная версия для построения графиков"""
    return np.where(x >= 0, x**n, 0.0)