"""Генератор пояснительной записки DOCX в логике образца преподавателя."""
from __future__ import annotations
import io
import math
from datetime import datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from model import Calculation
from plotter import png_bytes


def fnum(x, digits=3):
    if abs(x)<.5*10**(-digits): x=0.
    return f'{x:.{digits}f}'.replace('.',',')


def _set_cell_shading(cell, color='EAF2F9'):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:fill'),color); tcPr.append(shd)


def _set_font(run, size=None, bold=None):
    run.font.name='Times New Roman'
    if size:run.font.size=Pt(size)
    if bold is not None:run.bold=bold


def para(doc, text='', boldlead=None, align=None, size=None, spaceafter=4):
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(spaceafter)
    p.paragraph_format.line_spacing=1.10
    if align is not None:p.alignment=align
    if boldlead and text.startswith(boldlead):
        _set_font(p.add_run(boldlead),size,True)
        _set_font(p.add_run(text[len(boldlead):]),size)
    else:
        _set_font(p.add_run(text),size)
    return p


def heading(doc,text,level=2):
    p=doc.add_paragraph(style='Heading '+str(level))
    p.paragraph_format.space_before=Pt(8)
    p.paragraph_format.space_after=Pt(5)
    p.paragraph_format.keep_with_next=True
    _set_font(p.add_run(text),13 if level==1 else 11.5,True)
    return p


def table(doc,headers,rows,widths=None,font_size=9):
    t=doc.add_table(rows=1,cols=len(headers))
    t.style='Table Grid'
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    for j,name in enumerate(headers):
        c=t.rows[0].cells[j]; c.text=str(name);_set_cell_shading(c)
        for p in c.paragraphs:
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:_set_font(r,font_size,True)
    for row in rows:
        cells=t.add_row().cells
        for j,item in enumerate(row):
            cells[j].text=str(item)
            cells[j].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cells[j].paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:_set_font(r,font_size)
    if widths:
        for row in t.rows:
            for idx,cell in enumerate(row.cells):cell.width=Cm(widths[idx])
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return t


def _break(doc):
    doc.add_page_break()


def create_report(c:Calculation,path:str):
    s=c.s
    d=Document()
    sec=d.sections[0]
    sec.page_height=Cm(29.7);sec.page_width=Cm(21)
    sec.top_margin=Cm(2);sec.bottom_margin=Cm(2)
    sec.left_margin=Cm(2);sec.right_margin=Cm(2)
    sec.header_distance=Cm(.75);sec.footer_distance=Cm(1)
    norm=d.styles['Normal'];norm.font.name='Times New Roman';norm.font.size=Pt(10.5)
    norm.paragraph_format.space_after=Pt(4)
    for name in ('Heading 1','Heading 2'):
        st=d.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(18,35,58)
    # Automatic page number in footer.
    ft=sec.footer.paragraphs[0];ft.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    _set_font(ft.add_run('Лист '),9)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');ft._p.append(fld)
    # TITLE — A4, centered blocks like the supplied teacher example (not claimed exact torsion method template).
    para(d,'Федеральное государственное автономное образовательное учреждение',align=WD_ALIGN_PARAGRAPH.CENTER,size=10.5,spaceafter=0)
    para(d,'высшего образования «Омский государственный технический университет»',align=WD_ALIGN_PARAGRAPH.CENTER,size=10.5,spaceafter=55)
    para(d,'Кафедра «Машиноведение»',align=WD_ALIGN_PARAGRAPH.CENTER,size=11,spaceafter=72)
    para(d,s.title_task.upper(),align=WD_ALIGN_PARAGRAPH.CENTER,size=15,spaceafter=24)
    para(d,'по дисциплине',align=WD_ALIGN_PARAGRAPH.CENTER,size=12,spaceafter=7)
    para(d,'«СОПРОТИВЛЕНИЕ МАТЕРИАЛОВ»',align=WD_ALIGN_PARAGRAPH.CENTER,size=14,spaceafter=16)
    para(d,'по теме «Кручение»',align=WD_ALIGN_PARAGRAPH.CENTER,size=13,spaceafter=24)
    para(d,'Вариант: '+(s.title_variant or '________________'),align=WD_ALIGN_PARAGRAPH.CENTER,size=12,spaceafter=60)
    p=para(d,'Выполнил: студент гр. '+(s.title_group or '______________'),size=11,spaceafter=6)
    p.paragraph_format.left_indent=Cm(7.4)
    p=para(d,(s.title_student or 'Ф.И.О. ______________________')+'       __________',size=11,spaceafter=6);p.paragraph_format.left_indent=Cm(7.4)
    p=para(d,'Дата: '+(s.title_date or '________________'),size=11,spaceafter=6);p.paragraph_format.left_indent=Cm(7.4)
    p=para(d,'Проверил: '+(s.title_teacher or '________________'),size=11,spaceafter=6);p.paragraph_format.left_indent=Cm(7.4)
    p=para(d,'Дата: __________________',size=11,spaceafter=50);p.paragraph_format.left_indent=Cm(7.4)
    para(d,'Омск – '+(s.title_year or '2026'),align=WD_ALIGN_PARAGRAPH.CENTER,size=11,spaceafter=0)
    _break(d)

    # Page 2: Task and assumptions.
    heading(d,'ЗАДАЧА 2. Кручение круглого вала.',1)
    para(d,'Дано: прямолинейный вал из четырёх участков; длины участков, сосредоточенные крутящие моменты, распределённые моменты, закрепление и геометрия сечений указаны ниже.',boldlead='Дано:')
    table(d,['Параметр','Значение'],[
        ('Способ закрепления','Слева (z = 0)' if s.fixed=='left' else 'Справа (z = L)'),
        ('Общая длина L, м',fnum(c.coords[-1])),
        ('Модуль сдвига G, МПа',fnum(s.G_MPa)),
        ('Допускаемое напряжение [τ], МПа',fnum(s.tau_allow_MPa)),
        ('Допускаемый относительный угол [θ], рад/м',fnum(s.theta_allow_rad_m,5)),
        ('Поперечное сечение','Круглое (k = dвн/Dнар; k = 0 для сплошного)'),
    ],widths=[7.3,9.6],font_size=9.3)
    table(d,['Участок','ℓ, м','m, кН·м/м','Dнар, мм','k = dвн/Dнар'],[
        (str(i+1),fnum(s.lengths_m[i]),fnum(s.distributed_knm_per_m[i]),fnum(s.diameter_mm[i]),fnum(s.hole_ratio[i])) for i in range(4)
    ],widths=[2.3,2.5,4.3,3.4,4.3],font_size=8.8)
    para(d,'Сосредоточенные моменты в узлах z = 0; ℓ₁; ℓ₁+ℓ₂; ℓ₁+ℓ₂+ℓ₃; L:',spaceafter=3)
    table(d,['Узел','0','1','2','3','4'],[['M, кН·м']+[fnum(x) for x in s.node_moments_knm]],widths=[3.4,2.7,2.7,2.7,2.7,2.7],font_size=9)
    heading(d,'Требуется:',2)
    for line in [
        '1. Определить реактивный момент закрепления из условия равновесия.',
        '2. Записать уравнение крутящего момента Mк(z) на каждом из четырёх участков и вычислить восемь граничных значений.',
        '3. Построить в масштабе расчётную схему, эпюры крутящих моментов Mк(z) и углов закручивания φ(z).',
        '4. Проверить существующие сечения по прочности и жёсткости. Подобрать минимальные наружные диаметры по двум условиям с округлением вверх по нормальному ряду.',
        '5. Сформулировать вывод и ответ с размерностями.'
    ]:para(d,line,spaceafter=3)
    heading(d,'Принятые соглашения',2)
    para(d,'Ось z направлена слева направо. Внешний крутящий момент «+» действует по правилу правого винта вокруг +z. Внутренний Mк(z) противоположен сумме внешних моментов слева от сечения, включая реакцию при наличии левой заделки. Закон кручения: dφ/dz = Mк/(GJp). Расчёт применим к линейно-упругому круговому валу при малых углах закручивания.')
    para(d,'Внимание: это самостоятельный типовой вариант по кручению, а не официальный набор вариантов ОмГТУ. Значения [τ], [θ] и G пользователь должен сверить с выданным заданием.',size=9.5)
    _break(d)
    # Page 3: derive all four sections and table.
    heading(d,'Решение',1)
    heading(d,'1. Условие равновесия и закрепление',2)
    torques=[s.distributed_knm_per_m[i]*s.lengths_m[i] for i in range(4)]
    para(d,'Суммарный внешний момент ΣMвн = ΣMᵢ + Σ(mᵢℓᵢ) = '+fnum(sum(s.node_moments_knm))+' + '+fnum(sum(torques))+' = '+fnum(c.applied_sum)+' кН·м.')
    para(d,'Из ΣM_z = 0 получаем реакцию заделки: M_R = −ΣMвн = '+fnum(c.reaction_knm)+' кН·м.')
    para(d,('В заделке слева φ(0)=0.' if s.fixed=='left' else 'В заделке справа φ(L)=0.')+' На свободном торце внутренний крутящий момент однозначно следует из приложенного торцевого момента; другое граничное значение вычисляется по равновесию. Пользователь не вводит два независимых граничных условия.')
    heading(d,'2. Уравнения крутящих моментов на участках',2)
    para(d,'На участке i, где zᵢ₋₁ ≤ z ≤ zᵢ, принимаем Mк,i(z) = Mк,i(zᵢ₋₁+) − mᵢ · (z − zᵢ₋₁). Сосредоточенный момент в узле вызывает скачок ΔMк = −Mузла. Распределённый момент образует линейный наклон эпюры.')
    for i in range(4):
        para(d,f'{i+1}-й участок: {fnum(c.coords[i])} ≤ z ≤ {fnum(c.coords[i+1])} м.  '
               f'Mк,{i+1}(z) = {fnum(c.start_T[i])} − ({fnum(s.distributed_knm_per_m[i])})·(z − {fnum(c.coords[i])})  кН·м.',spaceafter=1)
        para(d,f'В начале: Mк = {fnum(c.start_T[i])} кН·м; в конце: Mк = {fnum(c.end_T[i])} кН·м.',spaceafter=5)
    heading(d,'3. Таблица восьми значений (по две границы каждого участка)',2)
    table(d,['Участок']+[f'{i+1}' for i in range(4)], [
        ['z слева, м']+[fnum(x) for x in c.coords[:-1]],
        ['Mк слева, кН·м']+[fnum(x) for x in c.start_T],
        ['z справа, м']+[fnum(x) for x in c.coords[1:]],
        ['Mк справа, кН·м']+[fnum(x) for x in c.end_T]
    ],widths=[4.7,3.1,3.1,3.1,3.1],font_size=9.2)
    worst=[]
    for i in range(4):
        if abs(c.max_T_per_segment[i]-c.max_T_knm)<1e-8: worst.append(str(i+1))
    para(d,f'Опасные по крутящему моменту участки: {", ".join(worst)}.  |Mк|max = {fnum(c.max_T_knm)} кН·м.',spaceafter=4)
    _break(d)

    # Page 4: diagram on its own page (teacher requirement).
    heading(d,'4. Расчётная схема и эпюры',1)
    para(d,'Схема, эпюра Mк(z) и эпюра углов закручивания φ(z) построены в едином масштабе по оси z. Вертикальные скачки Mк соответствуют сосредоточенным моментам, наклонные участки — распределённым моментам.')
    p=d.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(io.BytesIO(png_bytes(c)),width=Cm(16.6))
    para(d,'Положительные значения Mк соответствуют выбранному направлению скручивания. Угол φ непрерывен в каждом узле даже при скачке крутящего момента.',size=9.5)
    _break(d)

    # Page 5: strength & stiffness.
    heading(d,'5. Расчёт на прочность и жёсткость',1)
    para(d,'Для круглого сечения с наружным диаметром D и отношением k=dвн/D:')
    para(d,'Jp = πD⁴(1 − k⁴)/32, мм⁴;   Wp = πD³(1 − k⁴)/16, мм³.')
    para(d,'τmax = |Mк|max/Wp ≤ [τ];    θmax = |Mк|max/(GJp) ≤ [θ].')
    para(d,'Единицы: в формулах Mк переводится из кН·м в Н·мм (×10⁶), относительный угол из рад/мм в рад/м (×10³).')
    para(d,'Минимальный D по прочности = ∛[16·|Mк|max·10⁶ / (π·[τ]·(1−k⁴))].')
    para(d,'Минимальный D по жёсткости = ⁴√[32·|Mк|max·10⁹ / (π·G·[θ]·(1−k⁴))].')
    table(d,['Участок','|M|max, кН·м','τ, МПа','θ, рад/м','Dтр, мм','Dприн, мм'],[
        [str(i+1),fnum(c.max_T_per_segment[i]),fnum(c.tau_per_segment[i]),fnum(c.theta_per_segment[i],5),fnum(c.required_d[i]),fnum(c.recommended_d[i],0)] for i in range(4)
    ],widths=[1.7,3.0,2.4,3.0,3.4,3.4],font_size=8.7)
    para(d,'Здесь Dтр — больший из расчётов по прочности и жёсткости; Dприн — ближайшее большее значение из нормального ряда. При нулевом моменте на участке конструктивный минимальный диаметр программой принимается 1 мм; окончательное конструкторское решение требует иных проверок.')
    heading(d,'6. Эпюра углов закручивания',2)
    para(d,'φ(zᵢ) − φ(zᵢ₋₁) = (10⁹/(GJp,i))·[Mк,i(zᵢ₋₁+)·ℓᵢ − mᵢ·ℓᵢ²/2], рад.')
    para(d,'Нулевой угол поворота задан в заделке; интегрирование выполнено с учётом действительных диаметров каждого участка. При смене сечения φ остаётся непрерывным.')
    table(d,['z, м']+[fnum(x) for x in c.coords],[["φ, град"]+[fnum(v*180/math.pi) for v in c.phi_nodes]],widths=[3.3,2.7,2.7,2.7,2.7,2.7],font_size=9)
    heading(d,'Ответ:',2)
    ok_strength=c.max_tau_MPa <= s.tau_allow_MPa*(1+1e-9)
    ok_stiffness=c.max_theta_rad_m <= s.theta_allow_rad_m*(1+1e-9)
    para(d,f'M_R = {fnum(c.reaction_knm)} кН·м;   |Mк|max = {fnum(c.max_T_knm)} кН·м;   '
           f'τmax = {fnum(c.max_tau_MPa)} МПа;   θmax = {fnum(c.max_theta_rad_m,5)} рад/м;   max|φ| = {fnum(c.max_phi_rad*180/math.pi)}°.')
    para(d,f'Прочность: {"выполняется" if ok_strength else "НЕ выполняется"}. Жёсткость: {"выполняется" if ok_stiffness else "НЕ выполняется"}. '
           f'Рекомендуемые диаметры по участкам: '+', '.join(f'{x:g}' for x in c.recommended_d)+' мм.')
    heading(d,'Учебные источники и методическая основа',2)
    for src in [
        '1. Программа ОмГТУ по дисциплине «Техническая механика»: тема «Кручение. Методика расчёта конструкций на прочность и жёсткость» — omgtu.ru.',
        '2. Методические указания ЮЗГУ «Расчёт валов на кручение»: эпюра, подбор сечения по прочности и жёсткости — swsu.ru.',
        '3. Учебные материалы МГСУ «Кручение стержней круглого сечения»: Jp, Wp, угол закручивания — ektu.kz.',
    ]:para(d,src,size=8.5,spaceafter=1)
    d.save(path)
    return path
