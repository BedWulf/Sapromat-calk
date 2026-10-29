"""Продольные силы и перемещения стержня.

Принято: ось z слева направо, N>0 при растяжении, нагрузки
вправо положительны. Для внутренних сил dN/dz=-q_z, [N]=-P_z.
"""
from .rod import Rod
from .loads import ConcentratedForce, DistributedLoad
from .macaulay import macaulay


class Calculator:
    def __init__(self, rod: Rod):
        self.rod = rod
        if rod.total_length <= 0 or rod.n_segments < 1:
            raise ValueError('Длина стержня и число участков должны быть положительными')
        if rod.boundary_N_left is None and rod.boundary_N_right is None:
            raise ValueError('Не задано граничное условие N(0) или N(L)')
        for ld in rod.loads:
            if not 0 <= ld.start <= rod.total_length:
                raise ValueError('Сила/нагрузка вне длины стержня')
            if isinstance(ld, DistributedLoad) and not ld.start < ld.end <= rod.total_length:
                raise ValueError('Начало распределённой нагрузки должно предшествовать концу')
        if rod.boundary_N_left is not None and rod.boundary_N_right is not None:
            expected = rod.boundary_N_left - self._total_internal_load()
            if abs(expected - rod.boundary_N_right) > 1e-7:
                raise ValueError('Два граничных условия противоречат уравнению равновесия')

    def _total_internal_load(self):
        return sum(ld.direction.value * (ld.magnitude if isinstance(ld, ConcentratedForce)
                    else ld.intensity * (ld.end - ld.start)) for ld in self.rod.loads)

    def _N0(self):
        if self.rod.boundary_N_left is not None:
            return self.rod.boundary_N_left
        return self.rod.boundary_N_right + self._total_internal_load()

    def N(self, z: float) -> float:
        """N(z) [кН], правостороннее значение при сосредоточенной силе."""
        if not 0 <= z <= self.rod.total_length:
            raise ValueError('Координата z вне стержня')
        result = self._N0()
        for ld in self.rod.loads:
            if isinstance(ld, ConcentratedForce):
                result -= ld.direction.value * ld.magnitude * macaulay(z - ld.start, 0)
            else:
                q = ld.direction.value * ld.intensity
                result -= q * (macaulay(z-ld.start, 1) - macaulay(z-ld.end, 1))
        return result

    def boundary_values(self) -> dict:
        """Оба граничных значения [кН], полученные из одного известного Г.У.

        N(L) = N(0) - сумма проекций внутренних сосредоточенных сил
                         - интеграл продольных распределённых нагрузок.
        """
        return {'N_left': self._N0(),
                'N_right': self._N0() - self._total_internal_load()}

    def support_reaction(self) -> float:
        """Проекция реакции заделки на +z [кН], из ΣFz=0.

        Внешние силы непосредственно на закреплённом торце не влияют
        на N(z) внутри стержня, но учитываются при поиске реакции.
        """
        if getattr(self.rod, 'support_side', None) not in ('left', 'right'):
            raise ValueError('Для реакции укажите сторону закрепления')
        return -(getattr(self.rod, 'free_end_load', 0.0)
                 + self._total_internal_load()
                 + getattr(self.rod, 'support_load_at_fixed', 0.0))

    def _compute_N_from_right_boundary(self, z: float) -> float:
        """Сохранено для совместимости с предыдущими версиями."""
        return self.N(z)

    def _N_side(self, z: float, side: str) -> float:
        """Точное N(z-)/N(z+) без искусственных малых смещений."""
        if side not in ('left','right'):
            raise ValueError("side должен быть 'left' или 'right'")
        result = self._N0()
        for ld in self.rod.loads:
            if isinstance(ld, ConcentratedForce):
                if ld.start < z or (ld.start == z and side == 'right'):
                    result -= ld.direction.value * ld.magnitude
            else:
                overlap = max(0., min(z, ld.end) - ld.start)
                result -= ld.direction.value * ld.intensity * overlap
        return result

    def get_critical_coordinates(self):
        """Разделение в точках изменения q и приложения P, в том числе нестандартных."""
        L = self.rod.total_length
        coords = set(self.rod.get_segment_boundaries()) | {0., L}
        for ld in self.rod.loads:
            coords.add(float(ld.start))
            if isinstance(ld, DistributedLoad):
                coords.add(float(ld.end))
        return sorted(coords)

    def compute_at_boundaries(self) -> dict:
        """Таблица преподавателя: 4 участка / 8 значений на их границах.

        При нагрузках внутри участка для полной эпюры используйте
        compute_at_load_breakpoints().
        """
        boundaries = self.rod.get_segment_boundaries()
        return {f'участок_{i}': {'z_start': a, 'z_end': b,
                                'N_start': self._N_side(a,'right'),
                                'N_end': self._N_side(b,'left')}
                for i, (a,b) in enumerate(zip(boundaries,boundaries[1:]),1)}

    def compute_at_load_breakpoints(self):
        """Все интервалы постоянного q — эпюра без потери внутренних скачков."""
        boundaries = self.get_critical_coordinates()
        return [{'z_start': a, 'z_end': b,
                 'N_start': self._N_side(a,'right'),
                 'N_end': self._N_side(b,'left')}
                for a,b in zip(boundaries,boundaries[1:])]

    def find_dangerous_section(self) -> tuple:
        """Максимум |N| на концах всех интервалов, включая оба края скачка."""
        candidates = [(item['z_start'], item['N_start']) for item in self.compute_at_load_breakpoints()]
        candidates += [(item['z_end'], item['N_end']) for item in self.compute_at_load_breakpoints()]
        z, N = max(candidates, key=lambda item: abs(item[1]))
        return z, abs(N)

    def _integral_N_from_zero(self, z):
        """Аналитический интеграл N(z) dz [кН·м]."""
        if not 0 <= z <= self.rod.total_length:
            raise ValueError('Координата вне стержня')
        area = 0.
        for interval in self.compute_at_load_breakpoints():
            a, b = interval['z_start'], interval['z_end']
            if z <= a:
                break
            d = min(z,b)-a
            n0, n1 = interval['N_start'], interval['N_end']
            area += n0*d + (n1-n0)*d*d/(2*(b-a))
            if z <= b:
                break
        return area

    def W(self, z: float, F: float) -> float:
        """Перемещение относительно закреплённого конца [м]; без дискретизации."""
        if F <= 0 or self.rod.E <= 0:
            raise ValueError('Площадь F и модуль E должны быть положительными')
        is_left_fixed = getattr(self.rod,'support_side',None) == 'left'
        if getattr(self.rod,'support_side',None) is None:
            is_left_fixed = self.rod.boundary_N_right is not None and self.rod.boundary_N_left is None
        integral = self._integral_N_from_zero(z)
        if not is_left_fixed:
            integral -= self._integral_N_from_zero(self.rod.total_length)
        return integral * 1000. / (self.rod.E * F)

    def find_W_max(self, F: float) -> tuple:
        """Экстремум |W| на границах и в точках N(z)=0 (где W'(z)=0)."""
        candidates = self.get_critical_coordinates()
        for interval in self.compute_at_load_breakpoints():
            n0, n1 = interval['N_start'], interval['N_end']
            if n0*n1 < 0:
                a,b = interval['z_start'], interval['z_end']
                candidates.append(a + (b-a)*(-n0)/(n1-n0))
        zmax = max(sorted(set(candidates)), key=lambda z: abs(self.W(z,F)))
        return zmax, abs(self.W(zmax,F)), self.W(0.,F)
