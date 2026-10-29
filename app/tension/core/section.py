"""Подбор типоразмеров: минимальное сечение по прочности и (отдельно) жёсткости."""
from .standards import round_to_standard
import math


class SectionSelector:
    @staticmethod
    def from_area(F_min: float, shape: str) -> dict:
        if F_min < 0 or not math.isfinite(F_min):
            raise ValueError('Площадь должна быть неотрицательной и конечной')
        if shape == 'square':
            a = round_to_standard(math.sqrt(F_min))
            return {'a': a, 'F': a*a, 'shape': shape}
        if shape == 'rectangle_2_1':
            b = round_to_standard(math.sqrt(F_min/2))
            return {'b':b, 'h':2*b, 'F':2*b*b, 'shape':shape}
        if shape == 'circle':
            d = round_to_standard(math.sqrt(4*F_min/math.pi))
            return {'d':d, 'F':math.pi*d*d/4, 'shape':shape}
        raise ValueError(f'Неизвестная форма сечения: {shape}')

    @staticmethod
    def from_strength(N_max_kN: float, sigma_allow_Pa: float, shape: str) -> dict:
        if N_max_kN < 0 or sigma_allow_Pa <= 0:
            raise ValueError('Нагрузка должна быть неотрицательной, допускаемое напряжение положительным')
        return SectionSelector.from_area(N_max_kN*1000/sigma_allow_Pa,shape)

    @staticmethod
    def from_stiffness(W_max_m, W_allow_coeff, l_m, E_Pa, N_max_kN, shape, calculator=None):
        """Точный подбор при calculator: интегрирование N(z) от закреплённого конца.

        Старый вызов без calculator выдавал Nmax*4l/(E*[W]): это не
        решение по фактическим перемещениям, поэтому теперь явно запрещён.
        """
        if calculator is None:
            raise ValueError('Для точного расчёта жёсткости передайте calculator=Calculator')
        if W_allow_coeff <= 0 or l_m <= 0 or E_Pa <= 0:
            raise ValueError('Для проверки жёсткости требуются [W]>0, l>0, E>0')
        if not math.isclose(calculator.rod.E, E_Pa, rel_tol=1e-10):
            raise ValueError('E_Pa не совпадает с модулем E в расчётной модели')
        # При F=1 м² перемещение пропорционально 1/F; отсюда F_min.
        _, w_unit_area, _ = calculator.find_W_max(1.)
        F_min = w_unit_area / (W_allow_coeff*l_m)
        return SectionSelector.from_area(F_min, shape)
