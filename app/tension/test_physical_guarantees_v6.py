"""Проверка граничных условий и механики НЕ через табличные N из самого калькулятора.

Аналитический метод сечений, равновесие и отражение схемы.
"""
import math
import random
import unittest
from core.problem import make_calculator
from core.variants import get_preset_scheme, get_variant_data


def independent_N(scheme, support, P, q, L, z):
    """N из равновесия ОТСЕЧЁННОЙ части (выбор свободного конца)."""
    parts = [ld for row in scheme for ld in row]
    if support == 'right':
        # Равновесие левой части: N(z) = -ΣFleft.
        acc = 0.0
        for ld in parts:
            if ld['type'] == 'force':
                if ld['position'] < z and ld['position'] != L:
                    acc += ld['direction'] * ld['count'] * P
            else:
                a, b = ld['start'], ld['end']
                acc += ld['direction'] * ld['count'] * q * max(0, min(z, b) - a)
        return -acc
    # Равновесие правой части: N(z) = ΣFright, включая правый свободный торец.
    acc = 0.0
    for ld in parts:
        if ld['type'] == 'force':
            if ld['position'] > z and ld['position'] != 0:
                acc += ld['direction'] * ld['count'] * P
        else:
            a, b = ld['start'], ld['end']
            acc += ld['direction'] * ld['count'] * q * max(0, b-max(z, a))
    return acc


def reflected(scheme,L):
    output=[[], [], [], []]
    for part in scheme:
        for ld in part:
            clone=dict(ld)
            clone['direction']=-ld['direction']
            if ld['type']=='force':
                clone['position']=L-ld['position']
                group=min(3,int((L-clone['position'])/(L/4)))
            else:
                clone['start'],clone['end']=L-ld['end'],L-ld['start']
                group=min(3,int(clone['start']/(L/4)))
            output[group].append(clone)
    return output


class IndependentPhysicsV6(unittest.TestCase):
    def test_900_cases_method_of_sections_not_internal_model(self):
        for scheme_id in range(1,31):
            for data_id in range(1,31):
                support,scheme=get_preset_scheme(scheme_id,1)
                P,q=get_variant_data(data_id)
                c=make_calculator(scheme,P,q,1,support)
                for z in (0.125,0.375,0.875,1.125,1.75,2.375,2.875,3.125,3.625,3.875):
                    self.assertAlmostEqual(c.N(z),independent_N(scheme,support,P,q,4,z),places=8,
                        msg=f'scheme {scheme_id} / data {data_id} / z {z}')
                # Индивидуальное равновесие всей системы: R + sum applied = 0.
                external=0
                for row in scheme:
                    for ld in row:
                        external += (ld['direction']*ld['count']*P if ld['type']=='force' else
                                     ld['direction']*ld['count']*q*(ld['end']-ld['start']))
                self.assertAlmostEqual(c.support_reaction()+external,0,places=8)

    def test_both_supports_mirror_symmetry_all_30(self):
        for idx in range(1,31):
            side,s=get_preset_scheme(idx,1)
            P,q=get_variant_data(idx)
            mirror=reflected(s,4)
            c=make_calculator(s,P,q,1,side)
            d=make_calculator(mirror,P,q,1,'right' if side=='left' else 'left')
            for z in (.125,.625,1.125,1.625,2.125,2.625,3.125,3.625):
                self.assertAlmostEqual(c.N(z),d.N(4-z),places=8, msg=f'#{idx}: {z}')
                self.assertAlmostEqual(c.W(z,.0005),-d.W(4-z,.0005),places=9)
            self.assertAlmostEqual(c.find_dangerous_section()[1],d.find_dangerous_section()[1],places=8)

    def test_nonstandard_coordinates_randomized(self):
        rng=random.Random(42568)
        for side in ('left','right'):
            for _ in range(300):
                l=rng.uniform(.2,2.0);L=4*l
                P=rng.uniform(.2,80);q=rng.uniform(.5,50)
                scheme=[[] for _ in range(4)]
                for _ in range(5):
                    x=rng.uniform(.01*L,.99*L)
                    scheme[0].append({'type':'force','position':x,'count':rng.uniform(.2,3),
                                      'direction':rng.choice([-1,1])})
                    a=rng.uniform(0,.8*L);b=rng.uniform(a+.02*L,L)
                    scheme[1].append({'type':'distributed','start':a,'end':b,
                                      'count':rng.uniform(.2,2.0),'direction':rng.choice([-1,1])})
                free=L if side=='left' else 0
                scheme[3].append({'type':'force','position':free,'count':rng.uniform(.2,4),
                                  'direction':rng.choice([-1,1])})
                c=make_calculator(scheme,P,q,l,side)
                for fr in (.03,.13,.33,.59,.81,.96):
                    z=L*fr
                    self.assertAlmostEqual(c.N(z),independent_N(scheme,side,P,q,L,z),places=7)
                self.assertAlmostEqual(c.support_reaction()+sum(
                    ld['direction']*ld['count']*(P if ld['type']=='force' else q*(ld['end']-ld['start']))
                    for row in scheme for ld in row),0,places=7)

    def test_force_at_fixed_support_changes_only_reaction(self):
        for side in ('left','right'):
            L=4.
            fixed=0 if side=='left' else 4
            free=4 if side=='left' else 0
            scheme=[[{'type':'force','position':free,'direction':1,'count':2}],[],[],[]]
            c0=make_calculator(scheme,10,0,support=side)
            scheme[1].append({'type':'force','position':fixed,'direction':-1,'count':3})
            c1=make_calculator(scheme,10,0,support=side)
            for z in (.5,1.5,2.5,3.5): self.assertAlmostEqual(c0.N(z),c1.N(z))
            self.assertAlmostEqual(c1.support_reaction()-c0.support_reaction(),30)

    def test_right_or_left_boundary_as_single_input(self):
        for idx in range(1,31):
            side,s=get_preset_scheme(idx,1)
            P,q=get_variant_data(idx)
            c=make_calculator(s,P,q,support=side)
            base=c.boundary_values()
            for preset in ({'N_left':base['N_left'],'N_right':None},
                           {'N_left':None,'N_right':base['N_right']}):
                d=make_calculator(s,P,q,support=side,boundary=preset)
                for key in base: self.assertAlmostEqual(d.boundary_values()[key],base[key])

if __name__=='__main__':unittest.main()
