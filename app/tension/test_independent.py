"""Независимые проверки по методу сечений: суммы внешних сил по одну сторону
сечения, интегральное перемещение, скачки, производные, размерность [σ]=Н/мм².
Запуск: python -m unittest discover -v
"""
import math
import random
import unittest
from core.variants import get_variant_data, get_preset_scheme
from core.problem import make_calculator
from core.rod import Rod
from core.calculator import Calculator
from core.loads import ConcentratedForce, DistributedLoad, Direction
from core.section import SectionSelector
from core.standards import STANDARD_SIZES_MM, round_to_standard


def independent_oracle(scheme, P, q, z, L, support):
    """N(z) независимо от Calculator: равновесие отсечённой части.
    Для опоры справа берётся левая свободная часть; для опоры слева — правая.
    """
    outside=0.
    for part in scheme:
        for ld in part:
            multiplier=ld['direction']*ld['count']
            if ld['type']=='force':
                x=ld['position']
                if support=='right' and x < z:
                    outside += multiplier*P
                if support=='left' and x > z:
                    outside += multiplier*P
            elif ld['type']=='distributed':
                a,b=ld['start'],ld['end']
                if support=='right':
                    outside += multiplier*q*max(0., min(z,b)-a)
                else:
                    outside += multiplier*q*max(0., b-max(z,a))
    return (-outside if support=='right' else outside)


class TestsAgainstIndependentEquilibrium(unittest.TestCase):
    def test_thirty_schemes_by_section_method_with_4_sets(self):
        rng=random.Random(20261027)
        for scheme_no in range(1,31):
            for case in range(4):
                P,q,l=(rng.uniform(1,35),rng.uniform(1,40),rng.uniform(0.3,2.5))
                support,scheme=get_preset_scheme(scheme_no,l)
                calc=make_calculator(scheme,P,q,l,support)
                for k in range(1,81):
                    z=4*l*(k+0.2141)/82
                    if any(ld['type']=='force' and abs(ld['position']-z)<1e-9
                           for group in scheme for ld in group):
                        continue
                    expected=independent_oracle(scheme,P,q,z,4*l,support)
                    with self.subTest(scheme=scheme_no,case=case,z=z):
                        self.assertAlmostEqual(calc.N(z),expected,places=8)
                # Изменение N = -q Δz на интервале без сосредоточенной силы.
                for interval in calc.compute_at_load_breakpoints():
                    mid=(interval['z_start']+interval['z_end'])/2
                    left=interval['z_start']
                    q_at_mid=sum(ld.direction.value*ld.intensity for ld in calc.rod.loads
                                 if isinstance(ld,DistributedLoad) and ld.start<mid<ld.end)
                    self.assertAlmostEqual(interval['N_end']-interval['N_start'],
                                           -q_at_mid*(interval['z_end']-left),places=8)

    def test_control_provided_by_teacher(self):
        support,scheme=get_preset_scheme(22,1)
        c=make_calculator(scheme,15,15,1,support)
        values=[n for d in c.compute_at_boundaries().values() for n in (d['N_start'],d['N_end'])]
        self.assertEqual(values,[45,45,45,15,15,15,30,30])
        sec=SectionSelector.from_strength(45,160e6,'rectangle_2_1')
        self.assertEqual((sec['b'],sec['h']),(.012,.024))
        self.assertAlmostEqual(45_000/sec['F']/1e6,156.25)

    def test_students_nika_and_gorbachev(self):
        checks=[(17,10,24,34,11,22,140.495867768595),
                (21,20,22,66,15,30,146.666666666667)]
        for scheme_no,P,q,nmax,b,h,sigma in checks:
            with self.subTest(scheme=scheme_no):
                support,scheme=get_preset_scheme(scheme_no,1)
                c=make_calculator(scheme,P,q,1,support)
                self.assertAlmostEqual(c.find_dangerous_section()[1],nmax)
                sec=SectionSelector.from_strength(nmax,160e6,'rectangle_2_1')
                self.assertAlmostEqual(sec['b']*1000,b)
                self.assertAlmostEqual(sec['h']*1000,h)
                self.assertAlmostEqual(nmax*1000/sec['F']/1e6,sigma)
                self.assertLess(nmax*1000/sec['F'],160e6)

    def test_exact_deflections_both_supports_and_internal_extremum(self):
        L=4
        # Растянутый стержень, постоянное усилие 100 кН.
        s=[[ ],[],[],[{'type':'force','direction':1,'count':1,'position':4}]]
        c=make_calculator(s,100,0,1,'left')
        self.assertAlmostEqual(c.W(0,0.001),0)
        self.assertAlmostEqual(c.W(4,0.001),0.002)
        self.assertAlmostEqual(c.find_W_max(0.001)[1],0.002)
        # Аналогичный стержень с опорой справа и силой -100 кН на левом торце.
        s=[[{'type':'force','direction':-1,'count':1,'position':0}],[],[],[]]
        c=make_calculator(s,100,0,1,'right')
        self.assertAlmostEqual(c.W(0,.001),-.002)
        self.assertAlmostEqual(c.W(4,.001),0)
        # Внутренний экстремум W там, где N меняет знак (z=2 м).
        s=[[{'type':'distributed','direction':-1,'count':1,'start':0,'end':4}],
           [],[],[{'type':'force','direction':1,'count':1,'position':4}]]
        c=make_calculator(s,4,2,1,'left')
        self.assertAlmostEqual(c.N(0),-4)
        self.assertAlmostEqual(c.N(4),4)
        z,w,_=c.find_W_max(0.001)
        self.assertAlmostEqual(z,2)
        self.assertAlmostEqual(w,4_000/(200e9*.001))

    def test_stiffness_difference_real_problem(self):
        s17, loads17=get_preset_scheme(17,1)
        c17=make_calculator(loads17,10,24,1,s17)
        area17=SectionSelector.from_stiffness(0,0.002,1,2e11,34,
                                               'rectangle_2_1',calculator=c17)
        self.assertAlmostEqual(area17['b']*1000,11)
        s21,loads21=get_preset_scheme(21,1)
        c21=make_calculator(loads21,20,22,1,s21)
        area21=SectionSelector.from_stiffness(0,0.002,1,2e11,66,
                                               'rectangle_2_1',calculator=c21)
        self.assertAlmostEqual(area21['b']*1000,16)
        self.assertAlmostEqual(c21.find_W_max(.00045)[1],0.0021)

    def test_custom_interior_concentrated_load_is_not_missed(self):
        scheme=[[{'type':'force','direction':1,'count':1,'position':.2}],
                [{'type':'force','direction':-1,'count':1.6,'position':1.3}],
                [],[{'type':'distributed','direction':1,'count':2,'start':3.1,'end':3.7}]]
        c=make_calculator(scheme,10,4,1,'right')
        critical=c.compute_at_load_breakpoints()
        coords=[x['z_start'] for x in critical]+[critical[-1]['z_end']]
        self.assertIn(1.3,coords)
        self.assertAlmostEqual(c._N_side(1.3,'right')-c._N_side(1.3,'left'),16)
        self.assertAlmostEqual(c.find_dangerous_section()[1],10)

    def test_standard_rounding_over_limit_rejected(self):
        self.assertEqual(round_to_standard(.010307),.011)
        self.assertEqual(round_to_standard(.014361),.015)
        with self.assertRaises(ValueError):
            round_to_standard(1.123)

class TestsPublishedNumericalExamples(unittest.TestCase):
    """Примеры с открытых учебных сайтов — независимые числовые значения."""

    @staticmethod
    def _tip_displacement(P_kN, A_m2, E_Pa, L):
        # Поддержка слева, осевое растяжение P на правом конце.
        s=[[ ],[],[],[{'type':'force','direction':1,'count':1,'position':L}]]
        c=make_calculator(s,P_kN,0,l=L/4,support='left',E=E_Pa)
        return c.N(L/2), c.W(L,A_m2)*1000

    def test_uniccm_fem_worked_example(self):
        # https://www.uniccm.com/finite-element-method-explained
        n,disp=self._tip_displacement(100,1000e-6,200e9,2)
        self.assertEqual(n,100)
        self.assertAlmostEqual(disp,1.0)
        self.assertAlmostEqual(n*1000/(1000e-6)/1e6,100)

    def test_published_round_bar(self):
        # https://testbook.com/question-answer/a-2-m-long-steel-rod-with-20-mm-diameter-experienc--6a197924bd8bbe6fd61c26ef
        a=math.pi*(0.020**2)/4
        n,disp=self._tip_displacement(40,a,200e9,2)
        self.assertEqual(n,40)
        self.assertAlmostEqual(disp,1.2732395447,places=7)

    def test_published_120kn_reference_case(self):
        # https://formulaxis.com/en/calculators/strength-of-materials/axial-stress-elongation/
        n,disp=self._tip_displacement(120,1500e-6,210e9,2)
        self.assertEqual(n,120)
        self.assertAlmostEqual(n*1000/(1500e-6)/1e6,80)
        self.assertAlmostEqual(disp,0.7619047619,places=7)


if __name__=='__main__':
    unittest.main()
