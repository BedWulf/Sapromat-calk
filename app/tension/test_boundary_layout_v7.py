"""Проверка свободного торца и отражения схем для 30 вариантов приложения 2."""
import math
import unittest
from core.problem import make_calculator
from core.variants import SCHEMES, get_preset_scheme, get_variant_data


class AllTeacherSchemesV7(unittest.TestCase):
    EXPECT_LEFT = {1,7,8,9,10,11,17,18,19,20,21,25,26,27,30}

    def test_every_preset_chooses_its_only_free_boundary(self):
        self.assertEqual(set(SCHEMES),set(range(1,31)))
        for number in range(1,31):
            support,scheme=get_preset_scheme(number,1.0)
            self.assertEqual(support,'left' if number in self.EXPECT_LEFT else 'right')
            for data_num in range(1,31):
                P,q=get_variant_data(data_num)
                with self.subTest(scheme=number,data=data_num):
                    calc=make_calculator(scheme,P,q,support=support)
                    values=calc.boundary_values()
                    x_free = 4.0 if support=='left' else 0.0
                    net_end_force=sum(ld['count']*P*ld['direction']
                        for group in scheme for ld in group
                        if ld['type']=='force' and abs(ld['position']-x_free)<1e-8)
                    known=values['N_right' if support=='left' else 'N_left']
                    self.assertAlmostEqual(known,net_end_force*(1 if support=='left' else -1))
                    other=values['N_left' if support=='left' else 'N_right']
                    self.assertAlmostEqual(values['N_left']-values['N_right'],calc._total_internal_load())
                    # Из второго конца также восстановим исходное, не вводя оба.
                    alternative={'N_left':other,'N_right':None} if support=='left' else {'N_left':None,'N_right':other}
                    check=make_calculator(scheme,P,q,support=support,boundary=alternative)
                    self.assertAlmostEqual(check.boundary_values()['N_left'],values['N_left'])
                    self.assertAlmostEqual(check.boundary_values()['N_right'],values['N_right'])

    def test_source_examples_free_end_signs(self):
        for number,P,q,n0,n4 in ((17,10,24,34,-10),(21,20,22,-46,0),(22,15,15,45,30)):
            support,scheme=get_preset_scheme(number,1)
            result=make_calculator(scheme,P,q,support=support).boundary_values()
            self.assertAlmostEqual(result['N_left'],n0)
            self.assertAlmostEqual(result['N_right'],n4)

if __name__=='__main__': unittest.main()
