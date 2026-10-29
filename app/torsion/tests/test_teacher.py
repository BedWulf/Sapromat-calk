import unittest, math, tempfile
from pathlib import Path
from model import Calculation,Settings
from teacher import DATA,SCHEMES,teacher_settings,example_teacher,strength_design
from teacher_plot import teacher_png_bytes
from teacher_report import create_report

class TestTeacherVariants(unittest.TestCase):
    def test_all_schemes_and_data(self):
        self.assertEqual(set(DATA),set(range(1,31)))
        self.assertEqual(set(SCHEMES),set(range(1,31)))
        for no, (fixed, nodes, dist) in SCHEMES.items():
            self.assertEqual(len(nodes),5)
            self.assertEqual(len(dist),4)
            self.assertIn(fixed,('left','right'))
            self.assertEqual(sum(abs(x) for x in nodes),0 if no==18 else 1)
            self.assertEqual(sum(bool(x) for x in dist)>=1,True)
            # Every standard figure has one support and four segments.
            for row in DATA:
                s=teacher_settings(row,no)
                c=Calculation(s)
                self.assertAlmostEqual(c.reaction_knm+c.applied_sum,0,places=8)
                self.assertEqual(s.lengths_m,[1,1,1,1])
                self.assertEqual(s.tau_allow_MPa,90.)
                self.assertEqual(s.fixed,fixed)
                if fixed=='left':
                    self.assertAlmostEqual(c.end_T[-1],s.node_moments_knm[-1])
                else:
                    self.assertAlmostEqual(c.start_T[0],-s.node_moments_knm[0])
                for i in range(3):
                    self.assertAlmostEqual(c.start_T[i+1]-c.end_T[i],-s.node_moments_knm[i+1])
                self.assertLessEqual(strength_design(c)['tau_solid'],90.+1e-6)
                self.assertLessEqual(strength_design(c)['tau_hollow'],90.+1e-6)

    def test_ambiguously_transcribed_figures(self):
        self.assertEqual(SCHEMES[15][2],(0,-1,0,2))
        self.assertEqual(SCHEMES[16][2],(1,0,2,0))
        self.assertEqual(SCHEMES[18][2],(0,1,0,-2))
        self.assertEqual(SCHEMES[27][2],(-1,2,2,0))

    def test_professor_example_numbers(self):
        c=Calculation(example_teacher())
        self.assertEqual([round(v) for i in range(4) for v in (c.start_T[i],c.end_T[i])],
                         [5,5,-5,10,10,10,10,0])
        self.assertAlmostEqual(c.reaction_knm,-5)
        d=strength_design(c)
        self.assertEqual((d['d_round'],d['D_hollow'],d['d_hollow']),(85,86,43))
        self.assertGreater(d['area_solid'],d['area_hollow'])

    def test_standard_scheme_11_differs_from_professor_example(self):
        standard=teacher_settings(1,11)
        self.assertEqual(standard.distributed_knm_per_m[1],-10)
        self.assertEqual(example_teacher().distributed_knm_per_m[1],-15)

    def test_images_and_word(self):
        for n in range(1,31):
            asset=Path(__file__).parent.parent/'assets'/f'scheme_{n:02}.png'
            self.assertGreater(asset.stat().st_size,1500)
        with tempfile.TemporaryDirectory() as tmp:
            for s in (example_teacher(),teacher_settings(23,4),teacher_settings(11,22)):
                c=Calculation(s)
                self.assertEqual(teacher_png_bytes(c)[:8],b'\x89PNG\r\n\x1a\n')
                p=Path(tmp)/f'work{s.teacher_scheme}.docx'
                create_report(c,str(p))
                self.assertGreater(p.stat().st_size,20000)
                from docx import Document
                d=Document(p)
                text=' '.join(x.text for x in d.paragraphs)
                self.assertIn('Сравнение веса',text)
                self.assertIn('ЗАДАЧА 2. Кручение',text)

if __name__=='__main__':unittest.main()
