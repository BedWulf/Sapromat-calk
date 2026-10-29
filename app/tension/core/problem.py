"""Единая точка преобразования схемы в математическую модель.

Нагрузки на самом свободном торце задают граничное условие,
а не повторно добавляются как внутренние сосредоточенные силы.
"""
from .rod import Rod
from .loads import ConcentratedForce, DistributedLoad, Direction
from .calculator import Calculator
import math


def make_calculator(scheme, P, q, l=1.0, support='right', boundary=None, E=2e11):
    if support not in ('left','right'):
        raise ValueError('Опора должна быть left или right')
    if not all(math.isfinite(v) for v in (l, P, q, E)):
        raise ValueError('P, q, l и E должны быть конечными числами')
    if l <= 0 or P < 0 or q < 0 or E <= 0:
        raise ValueError('Требуются l>0, E>0, P≥0, q≥0')
    L=4*l
    rod=Rod(total_length=L, n_segments=4)
    rod.support_side=support
    rod.E=E
    free_x = L if support=='left' else 0.
    end_force = 0.
    fixed_force = 0.
    for part in scheme:
        for ld in part:
            sign=ld['direction']
            if sign not in (-1,1):
                raise ValueError('Направление нагрузки должно быть +1 или -1')
            count=float(ld['count'])
            if not math.isfinite(count):
                raise ValueError('Множитель нагрузки должен быть конечным')
            if count < 0:
                raise ValueError('Множитель нагрузки не может быть отрицательным; используйте направление')
            direction=Direction.POSITIVE if sign==1 else Direction.NEGATIVE
            if ld['type']=='force':
                x=float(ld['position'])
                if not math.isfinite(x):
                    raise ValueError('Координата сосредоточенной силы не определена')
                if not 0 <= x <= L:
                    raise ValueError('Сила вне стержня')
                if abs(x-free_x)<1e-9:
                    end_force += sign*count*P
                elif x not in (0.,L):
                    rod.add_load(ConcentratedForce(start=x, direction=direction, magnitude=count*P))
                else:
                    fixed_force += sign*count*P
                # Сила на закреплённом торце изменяет реакцию, но не N внутри стержня.
            elif ld['type']=='distributed':
                a,b=float(ld['start']),float(ld['end'])
                if not all(map(math.isfinite,(a,b))):
                    raise ValueError('Границы распределённой нагрузки должны быть конечными')
                rod.add_load(DistributedLoad(start=a,end=b,direction=direction,intensity=count*q))
            else:
                raise ValueError('Неизвестный тип нагрузки')
    if boundary is None:
        boundary = {'N_left': -end_force if support=='right' else None,
                    'N_right': end_force if support=='left' else None}
    left,right=boundary.get('N_left'),boundary.get('N_right')
    if left is None and right is None:
        raise ValueError('Нужно граничное условие с одной стороны')
    if any(x is not None and not math.isfinite(float(x)) for x in (left,right)):
        raise ValueError('Граничное условие должно быть конечным числом')
    rod.support_load_at_fixed = fixed_force
    rod.free_end_load = end_force
    rod.set_boundary(left=left,right=right)
    calc = Calculator(rod)
    # При ручном вводе обязательно проверяем равновесие свободного торца:
    # одно математически заданное значение N не должно противоречить схеме.
    actual = calc.boundary_values()
    free_key = 'N_right' if support == 'left' else 'N_left'
    expected_free = end_force if support == 'left' else -end_force
    if not math.isclose(actual[free_key],expected_free,rel_tol=1e-9,abs_tol=1e-7):
        name = 'N(4l)' if support == 'left' else 'N(0)'
        raise ValueError(
            f'Введённое граничное условие противоречит нагрузкам на свободном конце: '
            f'{name} должно быть {expected_free:g} кН, а получается '
            f'{actual[free_key]:g} кН. Проверьте направление силы или опору.')
    return calc
