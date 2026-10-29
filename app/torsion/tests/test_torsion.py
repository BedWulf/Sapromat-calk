import math
import random
import tempfile
import unittest
from pathlib import Path
from model import Settings,Calculation,J_p,W_p,normal_up,demo_simple,demo_distributed

class TestTorsion(unittest.TestCase):
    def close(self,a,b,tol=1e-9):self.assertAlmostEqual(a,b,delta=tol*max(1.,abs(a),abs(b)))

    def test_constant_torque_left(self):
        s=Settings(node_moments_knm=[0,0,0,0,2])
        c=Calculation(s)
        self.close(c.reaction_knm,-2)
        for a,b in zip(c.start_T,c.end_T):self.close(a,2);self.close(b,2)
        self.close(c.phi(4),2*4*1e9/(s.G_MPa*J_p(60,0)))
        self.close(c.max_tau_MPa,2e6/W_p(60,0))

    def test_constant_torque_right(self):
        s=Settings(node_moments_knm=[3,0,0,0,0],fixed='right')
        c=Calculation(s)
        self.close(c.reaction_knm,-3)
        for a,b in zip(c.start_T,c.end_T):self.close(a,-3);self.close(b,-3)
        self.close(c.phi_nodes[4],0)
        self.close(c.phi_nodes[0],3*4*1e9/(s.G_MPa*J_p(60,0)))

    def test_distributed_torque(self):
        s=Settings(node_moments_knm=[0]*5,distributed_knm_per_m=[2,0,0,0])
        c=Calculation(s)
        self.close(c.reaction_knm,-2)
        self.close(c.start_T[0],2);self.close(c.end_T[0],0)
        self.close(c.phi_nodes[1],1e9/(s.G_MPa*J_p(60,0)))

    def test_concentrated_jump(self):
        s=Settings(node_moments_knm=[0,2,-3,1,0])
        c=Calculation(s)
        self.close(c.end_T[0]-c.start_T[1],2)
        self.close(c.end_T[1]-c.start_T[2],-3)
        self.close(c.end_T[2]-c.start_T[3],1)
        self.close(c.T(1,'left'),c.end_T[0]);self.close(c.T(1,'right'),c.start_T[1])

    def test_supported_load_does_not_change_internal_moment(self):
        a=Calculation(Settings(node_moments_knm=[0,0,0,0,2]))
        b=Calculation(Settings(node_moments_knm=[99,0,0,0,2]))
        self.assertEqual(a.start_T,b.start_T)
        c=Calculation(Settings(node_moments_knm=[2,0,0,0,0],fixed='right'))
        d=Calculation(Settings(node_moments_knm=[2,0,0,0,99],fixed='right'))
        self.assertEqual(c.start_T,d.start_T)

    def test_zero_torques(self):
        s=Settings(node_moments_knm=[0]*5)
        c=Calculation(s)
        self.close(c.max_phi_rad,0);self.close(c.max_T_knm,0)
        self.assertEqual(c.recommended_d,[1.]*4)

    def test_published_educational_strength_stiffness_benchmark(self):
        # ЮЗГУ, «Расчёт валов на кручение», §8: max T=2 кН·м,
        # G=80 000 МПа, [τ]=35 МПа, [θ]=0.003 рад/м.
        # Официальное решение: по прочности ≈66 мм,
        # по жёсткости ≈96 мм, выбирают D=100 мм.
        s=Settings(node_moments_knm=[0,0,0,0,2],tau_allow_MPa=35,
                   theta_allow_rad_m=.003,G_MPa=80000)
        c=Calculation(s)
        self.assertAlmostEqual(c.required_d_strength[0],66.3,delta=.25)
        self.assertAlmostEqual(c.required_d_stiffness[0],95.95,delta=.25)
        self.assertEqual(c.recommended_d[0],100)

    def test_hollow_polar_geometry(self):
        D=100.;k=.6
        self.close(J_p(D,k),math.pi*(D**4-(D*k)**4)/32)
        self.close(W_p(D,k),J_p(D,k)/(D/2))

    def test_manual_design(self):
        c=Calculation(Settings(node_moments_knm=[0,0,0,0,1]))
        st=(16e6/(math.pi*90))**(1/3)
        stiff=(32e9/(math.pi*80000*.002))**.25
        self.close(c.required_d_strength[0],st)
        self.close(c.required_d_stiffness[0],stiff)
        self.assertGreaterEqual(c.recommended_d[0],max(st,stiff))

    def test_variable_d_and_G(self):
        s=Settings(node_moments_knm=[0,0,0,0,1],diameter_mm=[40,50,60,70],hole_ratio=[0,.2,.4,.6],G_MPa=71000)
        c=Calculation(s)
        expected=sum(1e9*s.lengths_m[i]/(s.G_MPa*J_p(s.diameter_mm[i],s.hole_ratio[i])) for i in range(4))
        self.close(c.phi_nodes[-1],expected)

    def test_torque_zero_crossing_extrema_phi(self):
        s=Settings(node_moments_knm=[0,0,0,0,-1],distributed_knm_per_m=[2,0,0,0])
        c=Calculation(s)
        # On first interval T starts +1 and ends -1; extremum at z=.5
        self.close(c.T(.5),0)
        self.assertGreaterEqual(c.max_phi_rad,abs(c.phi(.5)))
        self.close(c.max_phi_rad,max(abs(c.phi(x/100)) for x in range(401)),tol=1e-5)

    def test_mirror(self):
        a=Settings(lengths_m=[.7,1.3,.85,1.15],node_moments_knm=[1,-2,1.4,-.8,3.2],distributed_knm_per_m=[.25,-.15,.9,-.7],diameter_mm=[60,65,55,70],hole_ratio=[0,.2,.3,.4],fixed='left')
        b=Settings(lengths_m=a.lengths_m[::-1],node_moments_knm=[-v for v in a.node_moments_knm[::-1]],distributed_knm_per_m=[-v for v in a.distributed_knm_per_m[::-1]],diameter_mm=a.diameter_mm[::-1],hole_ratio=a.hole_ratio[::-1],fixed='right')
        x=Calculation(a);y=Calculation(b)
        for i in range(4):
            self.close(x.start_T[i],y.end_T[3-i]);self.close(x.end_T[i],y.start_T[3-i])
        self.close(x.max_tau_MPa,y.max_tau_MPa)
        for j in range(21):
            z=x.coords[-1]*j/20
            self.close(y.phi(z),-x.phi(x.coords[-1]-z),tol=1e-7)

    def test_normal_series(self):
        self.assertEqual(normal_up(12.001),14)
        self.assertEqual(normal_up(90),90)
        with self.assertRaises(ValueError):normal_up(1500)

    def test_input_validation(self):
        bad=[Settings(lengths_m=[1,1,1,0]),Settings(fixed='both'),Settings(hole_ratio=[0,0,1,0]),Settings(diameter_mm=[20,20,0,20]),Settings(tau_allow_MPa=-1)]
        for s in bad:
            with self.assertRaises(ValueError):Calculation(s)

    def test_random_equilibrium_and_exact_phi(self):
        rng=random.Random(42424)
        for _ in range(900):
            lengths=[rng.uniform(.11,1.7) for i in range(4)]
            s=Settings(lengths_m=lengths,node_moments_knm=[rng.uniform(-4,4) for i in range(5)],distributed_knm_per_m=[rng.uniform(-2,2) for i in range(4)],diameter_mm=[rng.uniform(38,110) for i in range(4)],hole_ratio=[rng.random()*.7 for i in range(4)],fixed=rng.choice(['left','right']))
            c=Calculation(s)
            self.close(c.reaction_knm,-sum(s.node_moments_knm)-sum(x*y for x,y in zip(lengths,s.distributed_knm_per_m)))
            for i in range(4):
                midpoint=(c.coords[i]+c.coords[i+1])/2
                self.close(c.T(midpoint),(c.start_T[i]+c.end_T[i])/2)
                analytic=1e9*(c.start_T[i]*lengths[i]-s.distributed_knm_per_m[i]*lengths[i]*lengths[i]/2)/(s.G_MPa*c.J[i])
                self.close(c.phi_nodes[i+1]-c.phi_nodes[i],analytic)
                self.assertGreaterEqual(c.recommended_d[i]+1e-9,c.required_d[i])
            self.assertLess(abs(c.phi_nodes[0 if s.fixed=='left' else 4]),1e-8)

    def test_roundtrip_and_offline_report(self):
        s=demo_distributed();t=Settings.from_json(s.to_json())
        self.assertEqual(s.node_moments_knm,t.node_moments_knm)
        from plotter import png_bytes
        from report import create_report
        c=Calculation(t)
        self.assertEqual(png_bytes(c)[:8],b'\x89PNG\r\n\x1a\n')
        with tempfile.TemporaryDirectory() as tmp:
            filename=str(Path(tmp)/'result.docx')
            create_report(c,filename)
            self.assertGreater(Path(filename).stat().st_size,30_000)
            from docx import Document
            words='\n'.join(p.text for p in Document(filename).paragraphs)
            self.assertIn('Кручение',words)
            self.assertIn('эпюры',words)

if __name__=='__main__':unittest.main()
