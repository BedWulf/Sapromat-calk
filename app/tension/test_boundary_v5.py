"""Граничные условия: оба конца, физическая совместимость, пользовательские координаты."""
import math
import unittest
from core.variants import get_variant_data,get_preset_scheme
from core.problem import make_calculator

class BoundaryV5Tests(unittest.TestCase):
    def test_900_combinations_both_boundary_values(self):
        for scheme_id in range(1,31):
            for data_id in range(1,31):
                P,q=get_variant_data(data_id)
                support,loads=get_preset_scheme(scheme_id,1.0)
                c=make_calculator(loads,P,q,support=support)
                n0,n4=c.boundary_values().values()
                self.assertAlmostEqual(n0-n4,c._total_internal_load(),places=8)
                self.assertAlmostEqual(n0,c.compute_at_boundaries()['участок_1']['N_start'],places=8)
                self.assertAlmostEqual(n4,c.compute_at_boundaries()['участок_4']['N_end'],places=8)
                if support=='right':
                    alt=make_calculator(loads,P,q,support=support,boundary={'N_left':None,'N_right':n4})
                else:
                    alt=make_calculator(loads,P,q,support=support,boundary={'N_left':n0,'N_right':None})
                self.assertAlmostEqual(alt.boundary_values()['N_left'],n0,places=8)
                self.assertAlmostEqual(alt.boundary_values()['N_right'],n4,places=8)

    def test_user_example_N0_minus_P_solves_N4(self):
        # Левый свободный конец: P направлена вправо, N0=-P.
        scheme=[[{'type':'force','position':0,'count':1,'direction':1}],
                [{'type':'distributed','start':1,'end':2,'count':1,'direction':1}],
                [{'type':'force','position':2,'count':2,'direction':-1}],[]]
        c=make_calculator(scheme,10,3,support='right',boundary={'N_left':-10,'N_right':None})
        self.assertEqual(c.boundary_values(),{'N_left':-10,'N_right':7.0})
        c2=make_calculator(scheme,10,3,support='right',boundary={'N_left':None,'N_right':7})
        self.assertEqual(c2.boundary_values(),{'N_left':-10,'N_right':7.0})

    def test_incorrect_manually_chosen_free_end_rejected(self):
        support,scheme=get_preset_scheme(22,1)
        with self.assertRaisesRegex(ValueError,'противоречит нагрузкам'):
            make_calculator(scheme,15,15,support=support,boundary={'N_left':44,'N_right':None})
        with self.assertRaisesRegex(ValueError,'противоречит нагрузкам'):
            make_calculator(scheme,15,15,support=support,boundary={'N_left':None,'N_right':29})
        with self.assertRaisesRegex(ValueError,'противоречат'):
            make_calculator(scheme,15,15,support=support,boundary={'N_left':45,'N_right':31})

    def test_arbitrary_interior_positions_and_distributed_spans(self):
        scheme=[[{'type':'force','position':0,'count':1,'direction':-1}],
                [{'type':'force','position':1.35,'count':1.5,'direction':1}],
                [{'type':'distributed','start':2.15,'end':3.65,'count':.8,'direction':-1}],[]]
        c=make_calculator(scheme,12,7,support='right')
        self.assertEqual(c.boundary_values()['N_left'],12)
        self.assertAlmostEqual(c.boundary_values()['N_right'],12-18+8.4)
        self.assertIn(1.35,c.get_critical_coordinates())
        self.assertIn(2.15,c.get_critical_coordinates())
        self.assertIn(3.65,c.get_critical_coordinates())

    def test_invalid_values_dont_silently_calculate(self):
        for value in [float('nan'),float('inf')]:
            with self.assertRaises(ValueError):
                make_calculator([[],[],[],[]],P=value,q=3)
            with self.assertRaises(ValueError):
                make_calculator([[],[],[],[]],P=3,q=4,l=value)

if __name__=='__main__': unittest.main()

class ManualDiagramTranscriptionTests(unittest.TestCase):
    def test_positions_corrected_from_original_figures(self):
        """Начала стрелок P на рисунках приложения 2 сверены вручную.
        Раньше код сдвигал силы на целый участок в схемах 1,9,15,18,25.
        """
        expected={1:(1,1),9:(1,1),15:(2,-1),18:(1,1),25:(1,2)}
        for number,(position,amplitude_or_sign) in expected.items():
            _,scheme=get_preset_scheme(number,1.)
            forces=[ld for group in scheme for ld in group if ld['type']=='force']
            target=forces[0] if number!=15 else forces[0]
            with self.subTest(scheme=number):
                self.assertEqual(target['position'],position)
                if number==25:self.assertEqual(target['count'],2)
                if number==15:self.assertEqual(target['direction'],-1)
