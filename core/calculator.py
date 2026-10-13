from .rod import Rod
from .loads import ConcentratedForce, DistributedLoad
from .macaulay import macaulay
import numpy as np


class Calculator:
    def __init__(self, rod: Rod):
        self.rod = rod

    def N(self, z: float) -> float:
       """Универсальное уравнение продольной силы [кН]"""
       if self.rod.boundary_N_left is not None:
           result = self.rod.boundary_N_left
       elif self.rod.boundary_N_right is not None:
           return self._compute_N_from_right_boundary(z)
       else:
           raise ValueError("Не задано граничное условие N(0) или N(4l)")

       for load in self.rod.loads:
           if isinstance(load, ConcentratedForce):
               result -= load.direction.value * load.magnitude * macaulay(z - load.start, 0)
           elif isinstance(load, DistributedLoad):
               q = load.direction.value * load.intensity
               result -= q * macaulay(z - load.start, 1)
               result += q * macaulay(z - load.end, 1)

       return result

    def _compute_N_from_right_boundary(self, z: float) -> float:
        """Вычислить N(z) если задано N(4l)"""
        N_right = self.rod.boundary_N_right

        total_load = 0
        for load in self.rod.loads:
            if isinstance(load, ConcentratedForce):
                total_load += load.direction.value * load.magnitude
            elif isinstance(load, DistributedLoad):
                q = load.direction.value * load.intensity
                total_load += q * (load.end - load.start)

        N_0 = N_right + total_load

        result = N_0
        for load in self.rod.loads:
            if isinstance(load, ConcentratedForce):
                result -= load.direction.value * load.magnitude * macaulay(z - load.start, 0)
            elif isinstance(load, DistributedLoad):
                q = load.direction.value * load.intensity
                result -= q * macaulay(z - load.start, 1)
                result += q * macaulay(z - load.end, 1)

        return result

    def compute_at_boundaries(self) -> dict:
        """Считает N в 8 точках (границы участков)"""
        boundaries = self.rod.get_segment_boundaries()
        results = {}
        epsilon = 0.001

        for i in range(len(boundaries) - 1):
            z_start = boundaries[i]
            z_end = boundaries[i + 1]

            # Для начала участка: берём значение СРАЗУ ПОСЛЕ точки
            # кроме самой первой точки z=0
            if i == 0:
                N_start = self.N(z_start)
            else:
                N_start = self.N(z_start + epsilon)

            # Для конца участка: берём значение СРАЗУ ПЕРЕД точкой
            # кроме самой последней точки z=4l
            if i == len(boundaries) - 2:
                N_end = self.N(z_end)
            else:
                N_end = self.N(z_end - epsilon)

            results[f"участок_{i+1}"] = {
                "z_start": z_start,
                "z_end": z_end,
                "N_start": N_start,
                "N_end": N_end
            }

        return results

    def find_dangerous_section(self) -> tuple:
        """Находит опасное сечение (максимальное |N|)"""
        boundaries = self.rod.get_segment_boundaries()
        max_N = 0
        dangerous_z = 0

        for z in boundaries:
            N_val = abs(self.N(z))
            if N_val > max_N:
                max_N = N_val
                dangerous_z = z

        return dangerous_z, max_N

    def W(self, z: float, F: float) -> float:
        """Перемещение W(z) [м] через интегрирование N(z)"""
        dz = 0.001
        z_array = np.arange(0, z + dz, dz)
        N_array = np.array([self.N(zi) * 1e3 for zi in z_array])

        integral = np.trapz(N_array, z_array)

        return integral / (self.rod.E * F)

    def find_W_max(self, F: float) -> tuple:
        """Находит максимальное перемещение"""
        boundaries = self.rod.get_segment_boundaries()
        max_W = 0
        dangerous_z = 0

        L = self.rod.total_length
        W_at_L = self.W(L, F)
        W_0 = -W_at_L

        for z in boundaries:
            W_val = abs(W_0 + self.W(z, F))
            if W_val > max_W:
                max_W = W_val
                dangerous_z = z

        return dangerous_z, max_W, W_0