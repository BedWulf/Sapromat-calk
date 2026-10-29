"""Инженерный расчёт кручения ступенчатого кругового вала с четырьмя участками.

Соглашение: z направлена слева направо; приложенный момент со знаком +
направлен по правилу правого винта вокруг +z; M_k=-сумма внешних
моментов слева от сечения; положительное M_k даёт d(phi)/dz>0.

Единицы ввода: m, кН·м, кН·м/м, мм, МПа, рад/м.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import json
import math

N = 4
NORMAL_MM = [1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,18,20,22,24,26,28,30,32,34,36,38,40,42,45,48,50,52,55,58,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200,205,210,215,220,225,230,235,240,245,250,260,270,280,290,300] + list(range(310,1001,10))

@dataclass
class Settings:
    lengths_m: list[float] = field(default_factory=lambda: [1.,1.,1.,1.])
    node_moments_knm: list[float] = field(default_factory=lambda: [2.,-3.,2.,-2.,1.])
    distributed_knm_per_m: list[float] = field(default_factory=lambda: [0.,0.,0.,0.])
    diameter_mm: list[float] = field(default_factory=lambda: [60.,60.,60.,60.])
    hole_ratio: list[float] = field(default_factory=lambda: [0.,0.,0.,0.])
    fixed: str = 'left'
    G_MPa: float = 80000.
    tau_allow_MPa: float = 90.
    theta_allow_rad_m: float = 0.002
    title_student: str = ''
    title_group: str = ''
    title_teacher: str = 'Онищук С.Ю.'
    title_variant: str = 'Свой вариант'
    title_year: str = '2026'
    title_date: str = ''
    title_task: str = 'Домашнее задание № 2'
    teacher_data_row: int = 0
    teacher_scheme: int = 0

    def validate(self) -> None:
        vectors = [('длины',self.lengths_m,4),('сосредоточенные моменты',self.node_moments_knm,5),('распределённые моменты',self.distributed_knm_per_m,4),('диаметры',self.diameter_mm,4),('коэффициенты полости',self.hole_ratio,4)]
        for label, arr, n in vectors:
            if len(arr) != n or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in arr):
                raise ValueError(f'{label}: необходимо {n} конечных чисел')
        if any(x <= 0 for x in self.lengths_m): raise ValueError('Длина каждого участка должна быть больше нуля')
        if any(x <= 0 for x in self.diameter_mm): raise ValueError('Наружный диаметр каждого участка должен быть больше нуля')
        if any(x < 0 or x >= 1 for x in self.hole_ratio): raise ValueError('Отношение d/D должно быть в диапазоне 0 ≤ d/D < 1')
        if self.fixed not in ('left','right'): raise ValueError('Закрепление: слева или справа')
        if (self.teacher_data_row != 0 or self.teacher_scheme != 0) and not (1 <= self.teacher_data_row <= 30 and 1 <= self.teacher_scheme <= 30): raise ValueError('Выберите оба номера: строку данных и схему нагружения')
        if self.G_MPa <= 0 or self.tau_allow_MPa <= 0 or self.theta_allow_rad_m <= 0 or not all(map(math.isfinite,(self.G_MPa,self.tau_allow_MPa,self.theta_allow_rad_m))):
            raise ValueError('G, [τ] и [θ] должны быть конечными положительными числами')

    @classmethod
    def from_json(cls, text: str) -> 'Settings':
        data = json.loads(text)
        if not isinstance(data,dict): raise ValueError('JSON должен содержать объект')
        allowed = set(cls.__dataclass_fields__)
        s = cls(**{k:v for k,v in data.items() if k in allowed})
        s.validate()
        return s

    def to_json(self) -> str:
        return json.dumps(asdict(self),ensure_ascii=False,indent=2)


def J_p(D: float, k: float) -> float:
    return math.pi * D**4 * (1.-k**4) / 32.

def W_p(D: float, k: float) -> float:
    return math.pi * D**3 * (1.-k**4) / 16.

def normal_up(value: float) -> float:
    for d in NORMAL_MM:
        if d >= value - 1e-10: return float(d)
    raise ValueError(f'Требуется наружный диаметр {value:.3f} мм, выходящий за заданный нормальный ряд до 1000 мм. Задайте другие допустимые значения либо масштаб нагрузок.')

class Calculation:
    def __init__(self, inp: Settings):
        inp.validate()
        self.s = inp
        self.coords = [0.]
        for L in inp.lengths_m: self.coords.append(self.coords[-1]+L)
        self.applied_sum = sum(inp.node_moments_knm) + sum(q*L for q,L in zip(inp.distributed_knm_per_m,inp.lengths_m))
        self.reaction_knm = -self.applied_sum
        # Reaction at support, including any independently applied torque there.
        self.start_T = []
        self.end_T = []
        if inp.fixed == 'left':
            current = -(self.reaction_knm + inp.node_moments_knm[0])
        else:
            current = -inp.node_moments_knm[0]
        for i in range(N):
            self.start_T.append(current)
            current = current - inp.distributed_knm_per_m[i]*inp.lengths_m[i]
            self.end_T.append(current)
            if i != N-1:
                current -= inp.node_moments_knm[i+1]
        self.J = [J_p(D,k) for D,k in zip(inp.diameter_mm,inp.hole_ratio)]
        self.W = [W_p(D,k) for D,k in zip(inp.diameter_mm,inp.hole_ratio)]
        self.max_T_per_segment = [max(abs(a),abs(b)) for a,b in zip(self.start_T,self.end_T)]
        self.max_T_knm = max(self.max_T_per_segment)
        self.tau_per_segment = [T*1e6/W for T,W in zip(self.max_T_per_segment,self.W)]
        self.theta_per_segment = [T*1e9/(inp.G_MPa*J) for T,J in zip(self.max_T_per_segment,self.J)]  # rad/m
        self.max_tau_MPa = max(self.tau_per_segment)
        self.max_theta_rad_m = max(self.theta_per_segment)
        self.required_d_strength = [(16*T*1e6/(math.pi*inp.tau_allow_MPa*(1-k**4)))**(1/3) for T,k in zip(self.max_T_per_segment,inp.hole_ratio)]
        self.required_d_stiffness = [(32*T*1e9/(math.pi*inp.G_MPa*inp.theta_allow_rad_m*(1-k**4)))**0.25 for T,k in zip(self.max_T_per_segment,inp.hole_ratio)]
        self.required_d = [max(a,b) for a,b in zip(self.required_d_strength,self.required_d_stiffness)]
        self.recommended_d = [normal_up(max(x,1.)) for x in self.required_d]
        self.recommended_common_d = max(self.recommended_d) if len(set(inp.hole_ratio))==1 else None
        # Exact integral of affine torque in each interval; length in meters.
        self.integrals = [1e9 * (a*L-0.5*q*L*L) /(inp.G_MPa*J) for a,q,L,J in zip(self.start_T,inp.distributed_knm_per_m,inp.lengths_m,self.J)]
        self.phi_nodes = [0.]
        for increment in self.integrals:
            self.phi_nodes.append(self.phi_nodes[-1]+increment)
        if inp.fixed == 'right':
            endpoint = self.phi_nodes[-1]
            self.phi_nodes = [x-endpoint for x in self.phi_nodes]
        self.max_phi_rad = self._exact_max_phi()
        self._self_audit()

    def _self_audit(self) -> None:
        s = self.s
        # At free end moment equals applied external torque, with signs determined by convention.
        residual = self.end_T[-1]-s.node_moments_knm[4] if s.fixed=='left' else self.start_T[0]+s.node_moments_knm[0]
        if abs(residual)>1e-8: raise AssertionError('Нарушено равновесие свободного торца')
        if abs(self.reaction_knm+self.applied_sum)>1e-8: raise AssertionError('Нарушено глобальное равновесие моментов')
        if abs(self.phi_nodes[0 if s.fixed=='left' else 4])>1e-8: raise AssertionError('Угол на заделке не равен нулю')
        for i in range(3):
            if abs(self.start_T[i+1]-(self.end_T[i]-s.node_moments_knm[i+1]))>1e-8:
                raise AssertionError('Неверный скачок эпюры')

    def section_for_x(self,x:float) -> int:
        if x < -1e-10 or x > self.coords[-1]+1e-10: raise ValueError('Координата вне вала')
        return next((i for i in range(4) if x < self.coords[i+1]-1e-10),3)

    def T(self,x:float,side:str='right') -> float:
        # side matters at concentrated torques, including at end of rod.
        if side not in ('left','right'): raise ValueError('side должен быть left или right')
        x = min(max(0.,x),self.coords[-1])
        for i in range(1,4):
            if abs(x-self.coords[i]) < 1e-10:
                return self.end_T[i-1] if side=='left' else self.start_T[i]
        i=self.section_for_x(x)
        return self.start_T[i]-self.s.distributed_knm_per_m[i]*(x-self.coords[i])

    def phi(self,x:float) -> float:
        x=min(max(x,0.),self.coords[-1])
        i=self.section_for_x(x)
        dx=x-self.coords[i]
        q=self.s.distributed_knm_per_m[i]
        return self.phi_nodes[i]+1e9*(self.start_T[i]*dx-q*dx**2/2)/(self.s.G_MPa*self.J[i])

    def _exact_max_phi(self) -> float:
        values=[abs(p) for p in self.phi_nodes]
        for i,q in enumerate(self.s.distributed_knm_per_m):
            if abs(q)>1e-14:
                dx=self.start_T[i]/q
                if 0<dx<self.s.lengths_m[i]:
                    x=self.coords[i]+dx
                    values.append(abs(self.phi(x)))
        return max(values)

    def manual_torque_check(self) -> dict[str,Any]:
        return {'reaction':self.reaction_knm,'moment_start':self.start_T[:],'moment_end':self.end_T[:], 'phi_nodes':self.phi_nodes[:], 'max_torque':self.max_T_knm}

    def sampled(self, points_each:int=28) -> tuple[list[float],list[float],list[float]]:
        x=[];T=[];phi=[]
        for i in range(4):
            for j in range(points_each+1):
                z=self.coords[i]+self.s.lengths_m[i]*j/points_each
                x.append(z)
                T.append(self.start_T[i]-self.s.distributed_knm_per_m[i]*(z-self.coords[i]))
                phi.append(self.phi(z))
        return x,T,phi


def demo_simple() -> Settings:
    return Settings(title_variant='Учебный пример А: четыре участка')

def demo_distributed() -> Settings:
    return Settings(lengths_m=[0.6,1.2,0.9,1.3],node_moments_knm=[1.2,-2.4,0.,3.,0.], distributed_knm_per_m=[0.6,-1.2,0.,0.8], diameter_mm=[55,65,65,75],hole_ratio=[0.,.25,.25,.4],fixed='right',title_variant='Учебный пример Б: ступенчатый вал')
