"""Исходные данные задачи №2 «Кручение», приложения 1–2 методички ОмГТУ 2026/27.

Координаты узлов: 0,l,2l,3l,4l. Для схем учтён знак на рисунке:
⊙ (точка над валом, + под ним) => положительный внешний момент,
⊕ (плюс над валом, точка под ним) => отрицательный внешний момент.
Результирующая внутренняя Mк = - сумма внешних моментов левее сечения.

В схеме значения записаны как (заделка, коэффициенты L в пяти узлах,
коэффициенты m на четырёх участках).
"""
from __future__ import annotations
from dataclasses import replace
from model import Settings, Calculation, NORMAL_MM
import math

# Строка таблицы -> (L, кН·м; m, кН·м/м). Прил. 1, задача № 2.
DATA = {
 1:(8,10),2:(6,15),3:(2,20),4:(2,25),5:(3,30),
 6:(3,10),7:(4,15),8:(4,20),9:(5,25),10:(5,30),
 11:(6,10),12:(6,15),13:(8,20),14:(8,25),15:(2,30),
 16:(2,10),17:(3,15),18:(3,20),19:(4,25),20:(4,30),
 21:(5,10),22:(5,15),23:(6,20),24:(6,25),25:(8,30),
 26:(8,10),27:(2,15),28:(2,20),29:(3,25),30:(3,30)
}
# Обозначения по фото схем приложения 2. Все распределённые нагрузки
# ограничены целыми участками; концентрированные приложены в узлах.
SCHEMES = {
  1:('left', (0,0,0,0,+1),(+1,0,-2,0)),
  2:('left', (0,0,0,0,+1),(+1,+2,0,0)),
  3:('left', (0,0,0,0,+1),(0,-2,0,-1)),
  4:('left', (0,0,0,0,+1),(0,+1,-2,-2)),
  5:('left', (0,0,0,0,+1),(+2,+2,-1,0)),
  6:('right',(-1,0,0,0,0),(0,-1,0,+2)),
  7:('right',(-1,0,0,0,0),(0,0,+2,+1)),
  8:('right',(-1,0,0,0,0),(+2,0,-1,0)),
  9:('right',(-1,0,0,0,0),(-1,+2,0,0)),
 10:('right',(-1,0,0,0,0),(0,-1,+2,0)),
 11:('left', (0,+1,0,0,0),(0,-1,0,+2)),
 12:('left', (0,0,0,0,-1),(+2,0,-1,0)),
 13:('left', (0,0,-1,0,0),(+1,0,0,-2)),
 14:('left', (0,0,0,+1,0),(0,-2,0,+1)),
 15:('left', (0,0,+1,0,0),(0,-1,0,+2)),
 16:('right',(0,-1,0,0,0),(+1,0,+2,0)),
 17:('left', (0,-1,0,0,0),(0,-1,0,+2)),
 18:('left', (0,0,0,0,0),(0,+1,0,-2)),
 19:('left', (0,0,0,0,+1),(0,-2,-1,0)),
 20:('left', (0,+1,0,0,0),(0,0,+2,-1)),
 21:('left', (0,0,-1,0,0),(0,+2,0,-1)),
 22:('right',(-1,0,0,0,0),(+2,0,-1,0)),
 23:('right',(0,0,-1,0,0),(+1,0,0,+2)),
 24:('right',(0,0,0,-1,0),(+1,0,-2,0)),
 25:('right',(0,0,-1,0,0),(-2,0,+1,0)),
 26:('right',(0,0,0,-1,0),(-1,-2,0,0)),
 27:('right',(0,0,-1,0,0),(-1,+2,+2,0)),
 28:('right',(-1,0,0,0,0),(0,+2,+1,0)),
 29:('right',(+1,0,0,0,0),(0,0,-2,-1)),
 30:('right',(0,0,+1,0,0),(-1,-2,0,0)),
}

def teacher_settings(row:int, scheme:int, previous:Settings|None=None) -> Settings:
    if row not in DATA:raise ValueError('Строка исходных данных должна быть 1–30')
    if scheme not in SCHEMES:raise ValueError('Схема должна быть 1–30')
    L, m = DATA[row]
    fixed, node, q = SCHEMES[scheme]
    src = previous if previous is not None else Settings()
    s = replace(src,
        fixed=fixed,lengths_m=[1.]*4,
        node_moments_knm=[x*L for x in node],
        distributed_knm_per_m=[x*m for x in q],
        tau_allow_MPa=90.,teacher_data_row=row,teacher_scheme=scheme,
        title_variant=(src.title_variant if previous is not None else f"Х-Х-{row}-{scheme}"))
    return s

def example_teacher() -> Settings:
    """Пример преподавателя (L=10, m=5): рисунок НЕ совпадает со схемой №11!
    В тексте примера во II участке приложено 3m, а в приложении №11 — m.
    """
    return Settings(lengths_m=[1]*4, node_moments_knm=[0,10,0,0,0],
        distributed_knm_per_m=[0,-15,0,10],fixed='left',
        tau_allow_MPa=90,teacher_data_row=0,teacher_scheme=0,
        title_variant='Учебный пример преподавателя: L=10; m=5')

def strength_design(c:Calculation):
    """Подбор двух сечений по условию прочности, как в образце:
    Wp=0.2*D**3*(1-k**4), k=0 для круга, 0.5 для кольца.
    Кольцевому сечению выбираем чётный наружный D, чтобы d=D/2
    был целым числом миллиметров, как в образце (D=86, d=43).
    """
    T=c.max_T_knm
    tau=c.s.tau_allow_MPa
    ds=(T*1e6/(.2*tau))**(1/3) if T else 0.
    dh=(T*1e6/(.2*tau*(1-0.5**4)))**(1/3) if T else 0.
    solid=next((v for v in NORMAL_MM if v>=ds-1e-10),None)
    hollow_std=next((v for v in NORMAL_MM if v>=dh-1e-10),None)
    if solid is None or hollow_std is None:raise ValueError('Требуемый диаметр превышает стандартный ряд 1000 мм')
    outer=hollow_std if hollow_std%2==0 else hollow_std+1
    inner=outer/2
    tau_s=T*1e6/(.2*solid**3) if T else 0.
    tau_h=T*1e6/(.2*outer**3*(1-.5**4)) if T else 0.
    fs=math.pi/4*solid**2
    fh=math.pi/4*(outer**2-inner**2)
    return {'d_round':solid,'D_hollow':outer,'d_hollow':inner,
       'required_solid':ds,'required_hollow':dh,'tau_solid':tau_s,'tau_hollow':tau_h,
       'area_solid':fs,'area_hollow':fh,'mass_ratio':fh/fs,'weight_saved_pct':100*(1-fh/fs)}

assert len(DATA)==len(SCHEMES)==30
