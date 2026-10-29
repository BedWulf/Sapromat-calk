"""Проверки схем, граничных условий и контрольного примера (без GUI)."""
import unittest
from core.variants import get_preset_scheme, get_variant_data
from core.rod import Rod
from core.loads import ConcentratedForce, DistributedLoad, Direction
from core.calculator import Calculator


def calculate_variant(scheme_number, P, q, l=1):
    support, scheme = get_preset_scheme(scheme_number, l)
    rod = Rod(total_length=4*l)
    for group in scheme:
        for item in group:
            if item['type'] == 'force':
                pos = item['position']
                if (support == 'right' and pos == 0) or (support == 'left' and pos == 4*l):
                    continue
                rod.add_load(ConcentratedForce(start=pos, magnitude=P*item['count'], direction=Direction.POSITIVE if item['direction'] == 1 else Direction.NEGATIVE))
            else:
                rod.add_load(DistributedLoad(start=item['start'], end=item['end'],
                                             intensity=q*item['count'], direction=Direction.POSITIVE if item['direction'] == 1 else Direction.NEGATIVE))
    free_pos = 0 if support == 'right' else 4*l
    F = sum(load['direction']*load['count']*P for group in scheme for load in group
            if load['type']=='force' and load['position']==free_pos)
    if support=='right': rod.set_boundary(left=-F)
    else: rod.set_boundary(right=F)
    return Calculator(rod)

class TestVariants(unittest.TestCase):
    def test_control_example(self):
        c = calculate_variant(22, 15, 15)
        actual = [round(value) for segment in c.compute_at_boundaries().values()
                  for value in (segment['N_start'], segment['N_end'])]
        self.assertEqual(actual, [45,45,45,15,15,15,30,30])
        self.assertEqual(c.find_dangerous_section(), (0,45))

    def test_all_variants_are_valid(self):
        for number in range(1,31):
            with self.subTest(number=number):
                P,q = get_variant_data(number)
                self.assertGreater(P,0);self.assertGreater(q,0)
                c=calculate_variant(number,P,q)
                data=c.compute_at_boundaries()
                self.assertEqual(len(data),4)
                for segment in data.values():
                    for key in ['N_start','N_end']:
                        self.assertLess(abs(segment[key]),1000)

    def test_scheme_17_nika_reference(self):
        # Схема №17 из задания: 2P при 2l, q вправо на [3l, 4l], -P при 4l.
        # Студенческая эпюра в docx отличается по знаку: это не эталон.
        c = calculate_variant(17, 10, 24)
        values = [round(n) for seg in c.compute_at_boundaries().values()
                  for n in (seg['N_start'], seg['N_end'])]
        self.assertEqual(values, [34, 34, 34, 34, 14, 14, 14, -10])
        self.assertAlmostEqual(c.find_dangerous_section()[1], 34)

    def test_scheme_21_gorbachev_reference(self):
        # Файл Zadacha_2_Gorbachev.docx: P при l, -q на [2l,3l], -2q на [3l,4l].
        c = calculate_variant(21, 20, 22)
        values = [round(n) for seg in c.compute_at_boundaries().values()
                  for n in (seg['N_start'], seg['N_end'])]
        self.assertEqual(values, [-46, -46, -66, -66, -66, -44, -44, 0])
        self.assertAlmostEqual(c.find_dangerous_section()[1], 66)

    def test_free_right_boundary(self):
        c = calculate_variant(17,15,12)
        # Сила P на свободном правом торце направлена влево: N(L) = -P.
        self.assertAlmostEqual(c.compute_at_boundaries()['участок_4']['N_end'],-15)

if __name__=='__main__': unittest.main()
