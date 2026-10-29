"""Генерация контрольных Word-файлов обновлённым экспортёром.
Не требует графического интерфейса (PyQt6).
"""
import os
from core.variants import get_preset_scheme
from core.problem import make_calculator
from core.section import SectionSelector
from export.word_exporter import WordExporter


def generate(path, scheme_id, P, q, l=1):
    support, scheme=get_preset_scheme(scheme_id,l)
    calc=make_calculator(scheme,P,q,l,support)
    boundaries=calc.compute_at_boundaries()
    danger=calc.find_dangerous_section()
    data={'P':P,'q':q,'l':l,'sigma_allow':160e6,'E':2e11,'W_coeff':0.002,
          'shape':1,'consider_stiffness':False}
    strong=SectionSelector.from_strength(danger[1],160e6,'rectangle_2_1')
    stiff=SectionSelector.from_stiffness(0,0.002,l,2e11,danger[1],
                                        'rectangle_2_1',calculator=calc)
    free_x=4*l if support=='left' else 0
    end_force=sum(ld['count']*P*ld['direction'] for group in scheme for ld in group
                   if ld['type']=='force' and abs(ld['position']-free_x)<1e-9)
    BC={'N_left':-end_force if support=='right' else None,
        'N_right':end_force if support=='left' else None}
    exp=WordExporter()
    exp.create_title_page({'student_name':'___________________',
                           'group':'__________',
                           'variant':f'__-__-__-{scheme_id}',
                           'teacher':'Онищук С.Ю.', 'date':'__________'})
    exp.add_calculation_text(data,boundaries,danger,strong,stiff,strong,
                             scheme=scheme,boundary_conditions=BC,
                             support_left=(support=='left'))
    exp.save(path)
    return {'scheme':scheme_id,'P':P,'q':q,'Nmax':danger[1],
            'b':strong['b']*1000,'h':strong['h']*1000,
            'sigma':danger[1]*1000/strong['F']/1e6,
            'b_stiffness_optional':stiff['b']*1000,
            'w_at_strength_mm':calc.find_W_max(strong['F'])[1]*1000,
            'path':path}

if __name__=='__main__':
    import json,sys
    output=sys.argv[1] if len(sys.argv)>1 else 'regression_examples'
    os.makedirs(output,exist_ok=True)
    checks=[('Prepodavatel_22',22,15,15),('Nika_17',17,10,24),('Gorbachev_21',21,20,22),
            ('Independent_01',1,7,16),('Independent_30',30,17,18)]
    for name,scheme,P,q in checks:
        p=os.path.join(output,f'{name}.docx')
        print(json.dumps(generate(p,scheme,P,q),ensure_ascii=False))
