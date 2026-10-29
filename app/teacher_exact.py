"""Подстановка вычислений в ОРИГИНАЛЬНЫЕ документы преподавателя ОмГТУ.

Не создаёт таблицы, заголовки и произвольные абзацы: используются исходные
OOXML, его поля, размеры, формулы/изображения, стили и разрывы страниц.
"""
from __future__ import annotations
import os, sys, io, math, copy, tempfile
from pathlib import Path
from docx import Document
from docx.shared import Pt
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parent
TEMPLATES=ROOT/'teacher_templates'

def fmt(v, n=3):
    if abs(v)<0.5*10**-n:v=0.
    return f'{v:.{n}f}'.rstrip('0').rstrip('.').replace('.',',')

def update(p, text, size=None):
    """Сохраняем абзац, выравнивание, поля, табуляцию, отступы и стили."""
    # Для текстовых формул исходник обычно содержит Times New Roman с жирностью.
    # Берём стиль первого непустого текстового run, но не удаляем OOXML картинок.
    runs=[r for r in p.runs if r.text.strip()]
    ref=max(runs, key=lambda r: len(r.text), default=None)
    fmt_r=copy.deepcopy(ref._r.rPr) if ref is not None and ref._r.rPr is not None else None
    for r in p.runs: r.text=''
    r=p.add_run(text)
    if fmt_r is not None:
        r._r.insert(0,fmt_r)
    if size:
        r.font.size=Pt(size)
    return p

def add_result(p, text):
    # Формульные изображения WMF из оригинала не затрагиваются.
    p.add_run('  '+text)

def title(doc, data, number):
    p=doc.paragraphs
    update(p[6],f'ДОМАШНЕЕ ЗАДАНИЕ № {number}')
    for i, text in [
       (15,'Вариант: '+str(data.get('variant') or '___-___-___-___')),
       (19,'Выполнил: ст. гр.'+str(data.get('group') or '________')),
       (20,str(data.get('student') or '________________')+' __________'),
       (21,'Дата:\t\t'+str(data.get('date') or '__________')),
       (22,'Проверил: '+str(data.get('position') or 'Ст. преп. каф.')),
       (24,str(data.get('teacher') or 'Онищук С.Ю.')+' _____________'),
       (25,'Дата:\t\t'+str(data.get('teacher_date') or '__________')),
       (28,'Омск – '+str(data.get('year') or '2026'))]:
        update(p[i],text)

def replace_png(doc,rid,png):
    part=doc.part.related_parts.get(rid)
    if part is None or part.content_type!='image/png':
        raise ValueError('Не найдено оригинальное изображение '+rid)
    # Подстановка байтов заменяет изображение В ИСХОДНОМ МЕСТЕ
    # без изменения размеров, привязок, обтекания и соседних элементов.
    part._blob=png

def adapt_png(blob,shape):
    img=Image.open(io.BytesIO(blob)).convert('RGB')
    # Без растягивания: масштабируем, дополняя белыми полями с пропорциями картинки преподавателя.
    bg=Image.new('RGB',shape,'white')
    inner=ImageOps.contain(img,(shape[0]-8,shape[1]-8),Image.Resampling.LANCZOS)
    bg.paste(inner,((shape[0]-inner.width)//2,(shape[1]-inner.height)//2))
    b=io.BytesIO();bg.save(b,'PNG');return b.getvalue()

def edit_math(paragraph, changes):
    """Правка ЧИСЕЛ внутри родных формул Word (OMML), не их замена картинкой."""
    ns='{http://schemas.openxmlformats.org/officeDocument/2006/math}t'
    ts=[x for x in paragraph._p.iter() if x.tag==ns]
    for i, val in changes.items():
        if i>=len(ts):raise ValueError('Изменилась структура формулы преподавателя')
        ts[i].text=str(val)

def text_title_from_env():
    import json
    try: return json.loads(os.environ.get('OMGTU_TITLE_JSON','{}'))
    except Exception: return {}

# ИСХОДНАЯ 1: РАСТЯЖЕНИЕ–СЖАТИЕ

def _axial_terms(calc, scheme, P, q, l):
    """Активационные члены для схем преподавателя: силa и кусочная q."""
    terms=[]
    for part in scheme:
        for ld in part:
            s=ld['direction']; k=ld['count']
            if ld['type']=='force':
                x=ld['position']/l
                # На торцах нет внутристержневого члена — оно входит в граничное условие/реакцию.
                if x<=1e-8 or x>=4-1e-8:continue
                terms.append((x,s,f'{fmt(k) if k!=1 else ""}P',None))
            elif ld['type']=='distributed':
                a=ld['start']/l;b=ld['end']/l
                def form(z):return f'{fmt(k) if k!=1 else ""}q(z − {fmt(z) if z!=1 else ""}l)' if z else f'{fmt(k) if k!=1 else ""}qz'
                terms.append((a,s,form(a),None))
                if b < 4 - 1e-8: terms.append((b,-s,form(b),None))
    terms.sort(key=lambda t:t[0])
    return terms

def _form_sum(terms, cutoff, flip=False):
    tokens=[]
    for x,s,txt,_ in terms:
        if x>cutoff+1e-10:continue
        ss=-s if flip else s
        tokens.append((' + ' if ss>0 else ' − ')+txt)
    return ''.join(tokens) if tokens else ''

def _boundary_8(calc):
    return [v for block in calc.compute_at_boundaries().values() for v in (block['N_start'],block['N_end'])]

def _tension_charts(calc, scheme, data, fixed):
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle
    l=data['l']
    def axes(ax,epure=False):
        ax.plot([0,4],[0,0],color='black',linewidth=1.8)
        wall=0 if fixed=='left' else 4
        ax.plot([wall,wall],[-.22,.25],color='black',linewidth=2)
        for t in range(6):
            yy=-.22+t*.075
            ax.plot([wall,wall+(-.12 if fixed=='left' else .12)],[yy,yy+.075],color='black',lw=.7)
        for i in range(5):
            ax.plot([i,i],[-.05,-.12],color='#444',lw=.6)
            ax.text(i,-.19,['0','l','2l','3l','4l'][i],ha='center',va='top',fontsize=12)
        for part in scheme:
            for ld in part:
                s=ld['direction'];count=ld['count']; typ=ld['type']
                lab=('' if count==1 else fmt(count))+('P' if typ=='force' else 'q')
                if typ=='force':
                    x=ld['position']/l
                    ax.annotate('',xy=(x+.25*s,.41),xytext=(x-.25*s,.41),arrowprops={'arrowstyle':'-|>','lw':1.25,'color':'black'})
                    ax.text(x,.59,lab,ha='center',fontsize=12)
                else:
                    a=ld['start']/l;b=ld['end']/l
                    for j in range(3):
                        x=a+(j+.5)*(b-a)/3
                        ax.annotate('',xy=(x+.12*s,.36),xytext=(x-.12*s,.36),arrowprops={'arrowstyle':'-|>','lw':1.15,'color':'black'})
                    ax.text((a+b)/2,.57,lab,ha='center',fontsize=12)
        ax.axis('off');ax.set_xlim(-.32,4.37);ax.set_ylim(-.35,.82)
    fig=Figure(figsize=(6.4,2.55),dpi=180,facecolor='white')
    ax=fig.add_subplot(111)
    axes(ax)
    b=io.BytesIO();fig.savefig(b,dpi=180,format='png',bbox_inches='tight',pad_inches=.07)
    fig=Figure(figsize=(7.1,6.85),dpi=155,facecolor='white')

    top=fig.add_axes([.08,.57,.85,.30]);axes(top)
    ep=fig.add_axes([.11,.11,.82,.45]);ep.axhline(0,color='black',lw=1)
    blocks=calc.compute_at_boundaries()
    vmax=max((abs(v) for v in _boundary_8(calc)),default=1) or 1
    for idx,part in enumerate(blocks.values()):
        x0=part['z_start']/l;x1=part['z_end']/l;y0=part['N_start'];y1=part['N_end']
        xx=[x0+(x1-x0)*j/70 for j in range(71)]; yy=[y0+(y1-y0)*j/70 for j in range(71)]
        ep.plot(xx,yy,color='#438fc0',lw=2.15)
        for j in range(1,16):
            x=x0+j*(x1-x0)/16;y=y0+(y1-y0)*(x-x0)/(x1-x0)
            ep.plot([x,x],[0,y],color='#555',lw=.52)
        ep.scatter([x0,x1],[y0,y1],s=10,color='#e77779',zorder=5)
        if idx>0:
            prev=list(blocks.values())[idx-1]['N_end']
            if abs(prev-y0)>1e-8:ep.plot([x0,x0],[prev,y0],color='#438fc0',lw=2.15)
        ep.text(x0+.04,y0+(vmax*.09 if y0>=0 else -vmax*.14),fmt(y0),fontsize=9)
    for i in range(5):ep.axvline(i,color='#777',lw=.55,alpha=.5)
    ep.set_xticks(range(5),['0','l','2l','3l','4l']);ep.set_yticks([])
    ep.set_xlim(-.25,4.37);ep.set_ylim(min(0,min(_boundary_8(calc)))-.32*vmax,max(0,max(_boundary_8(calc)))+.28*vmax)
    ep.text(2.15,max(_boundary_8(calc))*.95,'N(z), кН',fontsize=12)
    for edge in ep.spines.values():edge.set_visible(False)
    out=io.BytesIO();fig.savefig(out,format='png',dpi=155,facecolor='white')
    return b.getvalue(),out.getvalue()

def create_tension_docx(output, scheme, input_data, title_data, fixed='right', boundary=None, teacher_scheme=0):
    sys.path.insert(0,str(ROOT/'tension'))
    from core.problem import make_calculator
    from core.section import SectionSelector
    P=float(input_data['P']);q=float(input_data['q']);l=float(input_data['l'])
    sigma=float(input_data['sigma_allow'])/1e6
    calc=make_calculator(scheme,P,q,l=l,support=fixed,boundary=boundary,E=float(input_data.get('E',2e11)))
    eight=_boundary_8(calc);danger_z,danger_n=calc.find_dangerous_section()
    # Преподаватель для этой задачи требует h=2b; типоразмер — ближайшее большее.
    from core.standards import STANDARD_SIZES_MM
    b_req=math.sqrt(danger_n*1000/(2*sigma)) if danger_n>0 else 0
    normal=sorted(set(STANDARD_SIZES_MM))
    b=next((t for t in normal if t>=max(1,b_req)-1e-10),None)
    if b is None:raise ValueError('Ширина превышает нормальный ряд')
    h=2*b;tau=danger_n*1000/(b*h)
    d=Document(TEMPLATES/'teacher_tension.docx')
    title(d,title_data,1)
    # ЧИСЛА в существующих ячейках, формат и сетка Word сохраняются.
    for col,val in ((1,P),(2,q),(3,l),(4,sigma)):
        update(d.tables[0].cell(1,col).paragraphs[0],fmt(val))
    for i,v in enumerate(eight):update(d.tables[1].cell(2,i+1).paragraphs[0],fmt(v))
    terms=_axial_terms(calc,scheme,P,q,l)
    p=d.paragraphs
    def eq(end,flip=False):return 'N(z) = N(0)'+_form_sum(terms,end,flip)
    # Образец записывает исходное уравнение со скобками, затем раскрывает их.
    bracket=''.join((' + ' if s>0 else ' − ')+name+'│'+(['I','II','III','IV'][min(3,int(x))]) for x,s,name,_ in terms)
    update(p[36],'N(z)=N(0) − [ 0│I'+bracket+' ]',size=11)
    gu=calc.boundary_values();free='N(4l)' if fixed=='left' else 'N(0)'
    v=gu['N_right' if fixed=='left' else 'N_left']
    update(p[38],free+' = '+fmt(v)+' кН.')
    update(p[40],eq(4,flip=True),size=11)
    for i,ids in enumerate(((42,43,44),(45,46,47),(48,49,50),(51,52,53))):
        header, pa,pb=ids
        update(p[header],f'{["I","II","III","IV"][i]} участок  {"0" if i==0 else ("l" if i==1 else str(i)+"l")} ≤ z ≤ {"l" if i==0 else str(i+1)+"l"}.')
        for target,local,v in ((pa,i,eight[2*i]),(pb,i+1,eight[2*i+1])):
            zstr='0' if local==0 else ('l' if local==1 else f'{local}l')
            update(p[target],f'N({zstr}) = {eq(i+1-1e-6,flip=True).replace("N(z) = ","").replace("N(0)",fmt(gu["N_left"])) .replace("z",zstr)} = {fmt(v)} кН.',size=10.3)
    update(p[57],f'Опасное сечение z={fmt(danger_z)} м, |N|max={fmt(danger_n)} кН.')
    fmin_m2=danger_n*1000/sigma/1e6
    edit_math(p[61],{6:fmt(danger_n)+'∙',9:fmt(sigma)+'∙10',11:'='+fmt(fmin_m2*1000)+'∙'})
    edit_math(p[63],{4:fmt(fmin_m2*1000)+'∙',7:'='+fmt(b_req/1000,5)+'  '})
    update(p[64],f'Из нормального ряда выбираем значение b = {fmt(b)} мм. h = 2b = {fmt(h)} мм.')
    edit_math(p[66],{11:fmt(danger_n)+'∙',14:fmt(b)+'∙10',16:'∙'+fmt(h)+'∙10',18:'='+fmt(tau)+' МПа '})
    edit_math(p[67],{5:'='+fmt(sigma)+' МПа'})
    update(p[67],f'т.е. {fmt(tau)} МПа ≤ {fmt(sigma)} МПа, условие прочности выполняется.')
    scheme_png,epure_png=_tension_charts(calc,scheme,input_data,fixed)
    replace_png(d,'rId5',adapt_png(scheme_png,(316,133)))
    replace_png(d,'rId7',adapt_png(epure_png,(544,521)))
    d.save(output)
    return {'eight':eight,'Nmax':danger_n,'b':b,'h':h,'sigma':tau}

# ИСХОДНАЯ 2: КРУЧЕНИЕ

def _torsion_graph(calc):
    from matplotlib.figure import Figure
    from matplotlib.image import imread
    s=calc.s
    fig=Figure(figsize=(7.2,6.85),dpi=155,facecolor='white')
    top=fig.add_axes([.09,.59,.83,.28]);top.axis('off')
    if s.teacher_scheme:
        source=ROOT/'torsion'/'assets'/f'scheme_{s.teacher_scheme:02}.png'
        if source.exists():top.imshow(imread(str(source)),aspect='auto');top.set_xlim(0,imread(str(source)).shape[1]);top.set_ylim(imread(str(source)).shape[0],0)
    else:
        top.plot([0,4],[0,0],color='black',lw=2)
        w=0 if s.fixed=='left' else 4;top.plot([w,w],[-.5,.5],color='black',lw=2)
        for i,v in enumerate(s.node_moments_knm):
            if abs(v)>1e-9:top.text(i,.35,('⊙' if v>0 else '⊕')+fmt(abs(v)),fontsize=12,ha='center')
        for i,v in enumerate(s.distributed_knm_per_m):
            if abs(v)>1e-9:top.text(i+.5,.8,('⊙' if v>0 else '⊕')+fmt(abs(v)),fontsize=11,ha='center')
        top.set_xlim(-.25,4.3);top.set_ylim(-.5,1.5)
    ax=fig.add_axes([.115,.12,.80,.43]);ax.axhline(0,color='black',lw=1)
    allv=[v for i in range(4) for v in (calc.start_T[i],calc.end_T[i])]
    maxv=max((abs(v) for v in allv),default=1) or 1
    for i in range(4):
        a,b=calc.coords[i:i+2]
        xx=[a+(b-a)*j/60 for j in range(61)]; yy=[calc.start_T[i]-s.distributed_knm_per_m[i]*(x-a) for x in xx]
        ax.plot(xx,yy,color='#4399ca',lw=2)
        for j in range(1,17):
            x=a+j*(b-a)/17;y=calc.start_T[i]-s.distributed_knm_per_m[i]*(x-a)
            ax.plot([x,x],[0,y],color='#666',lw=.5)
        ax.scatter([a,b],[yy[0],yy[-1]],s=13,color='#dc7777',zorder=5)
        ax.annotate(fmt(yy[0]),(a,yy[0]),xytext=(4,6),textcoords='offset points',fontsize=9)
        if i and abs(calc.start_T[i]-calc.end_T[i-1])>1e-8:
            ax.plot([a,a],[calc.start_T[i],calc.end_T[i-1]],color='#4399ca',lw=1.6)
    for i in range(5):ax.axvline(calc.coords[i],color='#777',alpha=.45,lw=.7)
    ax.set_xticks(calc.coords,['0','l','2l','3l','4l']);ax.set_yticks([]);ax.set_xlim(-.15,calc.coords[-1]+.15)
    ax.set_ylim(min(0,min(allv))-.25*maxv,max(0,max(allv))+.25*maxv)
    ax.text(calc.coords[-1]*.26,max(allv)*.91,'Mк(z), кН·м',fontsize=12)
    for edge in ax.spines.values():edge.set_visible(False)
    output=io.BytesIO();fig.savefig(output,format='png',dpi=155);return output.getvalue()

def create_torsion_docx(output, calc, title_data):
    sys.path.insert(0,str(ROOT/'torsion'))
    from teacher import strength_design,DATA
    s=calc.s;dd=strength_design(calc)
    d=Document(TEMPLATES/'teacher_torsion.docx');title(d,title_data,2)
    if s.teacher_data_row:
        L,m=DATA[s.teacher_data_row]
        table_values=[fmt(L),fmt(m),fmt(s.lengths_m[0]),fmt(s.tau_allow_MPa)]
    else:
        # При произвольной схеме единственных L/m может не быть.
        # Не выдаём первую нагрузку за общие данные: всё показано на рисунке.
        same_lengths=all(abs(x-s.lengths_m[0])<1e-9 for x in s.lengths_m)
        table_values=['см. сх.','см. сх.',fmt(s.lengths_m[0]) if same_lengths else 'разн.',fmt(s.tau_allow_MPa)]
    for col,value in enumerate(table_values,1):
        update(d.tables[0].cell(1,col).paragraphs[0],value)
    eight=[v for i in range(4) for v in (calc.start_T[i],calc.end_T[i])]
    for i,v in enumerate(eight):update(d.tables[1].cell(2,i+1).paragraphs[0],fmt(v))
    variable_lengths=any(abs(t-s.lengths_m[0])>1e-9 for t in s.lengths_m)
    if variable_lengths:
        coords=[c for i in range(4) for c in (calc.coords[i],calc.coords[i+1])]
        for j,v in enumerate(coords):
            update(d.tables[1].cell(1,j+1).paragraphs[0],fmt(v))
    p=d.paragraphs
    # Уравнение для четырёх участков: активные сосредоточенные моменты
    # и начальные/компенсационные члены распределённых моментов.
    parts=[]
    for i in range(1,4):
        if abs(s.node_moments_knm[i])>1e-10:parts.append((i,-s.node_moments_knm[i],f'{fmt(abs(s.node_moments_knm[i]))}'))
    for i,q in enumerate(s.distributed_knm_per_m):
        if abs(q)>1e-10:
            start='z' if i==0 else (f'(z − {fmt(calc.coords[i])})' if variable_lengths else f'(z − {"" if i==1 else i}l)')
            end=(f'(z − {fmt(calc.coords[i+1])})' if variable_lengths else f'(z − {i+1 if i+1>1 else ""}l)')
            parts.append((i,-q,fmt(abs(q))+start))
            if i<3:parts.append((i+1,q,fmt(abs(q))+end))
    parts.sort(key=lambda t:t[0])
    def eq(cut):
        expr='Mк(0)'
        for a,v,name in parts:
            if a<=cut:expr+=(' + ' if v>0 else ' − ')+name
        return expr
    update(p[37],'Mк(z) = '+eq(4),size=10.8)
    fr='Mк(4l)' if s.fixed=='left' else 'Mк(0)'
    fv=calc.end_T[-1] if s.fixed=='left' else calc.start_T[0]
    update(p[38],f'4. Запишем граничные условия. Г.У.: {fr} = {fmt(fv)} кНм.')
    if s.fixed=='left':
        update(p[39],'5. Крутящий момент в нулевом сечении найдём из общего уравнения, подставив z = 4l, откуда выразим Mк(0):')
        update(p[40],'Mк(4l) = '+eq(4)+' = '+fmt(calc.end_T[-1])+' кНм.',size=10.5)
        update(p[41],f'Mк(0) = {fmt(calc.end_T[-1])} + ({fmt(sum(s.node_moments_knm[1:4])+sum(a*b for a,b in zip(s.distributed_knm_per_m,s.lengths_m)))}) = {fmt(calc.start_T[0])} кНм.')
    else:
        update(p[39],'5. Крутящий момент в конечном сечении найдём из общего уравнения, подставив z = 4l:')
        update(p[40],'Mк(4l) = '+eq(4)+' = '+fmt(calc.end_T[-1])+' кНм.',size=10.5)
        update(p[41],f'Mк(0) = {fmt(calc.start_T[0])} кНм, Mк(4l) = {fmt(calc.end_T[-1])} кНм.')
    update(p[43],f'ΣM_z = {fmt(calc.reaction_knm)} + ({fmt(calc.applied_sum)}) = 0.',size=11)
    update(p[44],f'Реактивный момент заделки Mр = {fmt(calc.reaction_knm)} кНм.')
    for i,(head,expridx,startidx,endidx) in enumerate(((47,48,49,50),(51,52,53,54),(55,56,57,58),(59,60,61,62))):
        segment_range=(f'{fmt(calc.coords[i])} ≤ z ≤ {fmt(calc.coords[i+1])} м.' if variable_lengths else
           f'{"0" if i==0 else str(i)+"l"} ≤ z ≤ {"l" if i==0 else str(i+1)+"l"}.')
        update(p[head],f'{["I","II","III","IV"][i]} участок  {segment_range}')
        update(p[expridx],'Mк(z) = '+eq(i),size=10.8)
        # Формулы с подстановкой граничных значений, как в учебном документе.
        ax='0' if i==0 else 'l' if i==1 else f'{i}l'
        bx='l' if i==0 else f'{i+1}l'
        update(p[startidx],f'Mк({ax}) = {fmt(calc.start_T[i])} кНм.')
        update(p[endidx],f'Mк({bx}) = {fmt(calc.start_T[i])} − ({fmt(s.distributed_knm_per_m[i])})·{fmt(s.lengths_m[i])} = {fmt(calc.end_T[i])} кНм.',size=10.7)
    update(p[63],'= '+fmt(calc.end_T[-1])+' кНм.')
    danger_idx=max(range(4),key=lambda i:max(abs(calc.start_T[i]),abs(calc.end_T[i])))
    danger_z=calc.coords[danger_idx] if abs(calc.start_T[danger_idx])>=abs(calc.end_T[danger_idx]) else calc.coords[danger_idx+1]
    update(p[66],f'Опасное сечение z={fmt(danger_z)} м, Mк.max = {fmt(calc.max_T_knm)} кНм.')
    w_m3=calc.max_T_knm*1000/(s.tau_allow_MPa*1e6)
    edit_math(p[69],{7:fmt(calc.max_T_knm)+'∙',10:fmt(s.tau_allow_MPa)+'∙10',12:'='+fmt(w_m3*1000)+'∙'})
    edit_math(p[71],{9:fmt(w_m3*1000)+'∙',13:'='+fmt(dd['required_solid'])+' мм'})
    update(p[72],f'Из нормального ряда выбираем значение dкр={fmt(dd["d_round"])} мм.')
    edit_math(p[74],{15:fmt(calc.max_T_knm),17:fmt(dd['d_round']),19:'='+fmt(dd['tau_solid'])+' МПа'})
    edit_math(p[75],{5:'='+fmt(s.tau_allow_MPa)+' МПа'})
    update(p[75],f'т.е. τкр = {fmt(dd["tau_solid"])} ≤ [τ] = {fmt(s.tau_allow_MPa)} МПа, условие прочности выполняется.')
    edit_math(p[77],{10:fmt(w_m3*1000)+'∙',17:'='+fmt(dd['required_hollow'])+' мм'})
    update(p[78],f'Принимаем: D = {fmt(dd["D_hollow"])} мм. d= D/α= {fmt(dd["D_hollow"])}/2 = {fmt(dd["d_hollow"])} мм.')
    edit_math(p[80],{18:fmt(calc.max_T_knm),20:fmt(dd['D_hollow']/1000,5),26:'='+fmt(dd['tau_hollow'])+' МПа'})
    edit_math(p[81],{5:'='+fmt(s.tau_allow_MPa)+' МПа'})
    update(p[81],f'т.е. τкол = {fmt(dd["tau_hollow"])} ≤ [τ] = {fmt(s.tau_allow_MPa)} МПа, условие прочности выполняется.')
    edit_math(p[83],{7:'3,14∙'+fmt(dd['d_round']/1000,5),9:'='+fmt(dd['area_solid']/1000)+'∙'})
    edit_math(p[84],{15:fmt(dd['D_hollow']/1000,5),18:fmt(dd['d_hollow']/1000,5),22:'='+fmt(dd['area_hollow']/1000)+'∙'})
    winner='кольцевое' if dd['area_hollow']<dd['area_solid'] else 'круглое'
    update(p[85],f'Т.к. Fкр {">" if winner=="кольцевое" else "≤"} Fкол, следовательно, mкр {">" if winner=="кольцевое" else "≤"} mкол, а значит {winner} сечение оптимальное.')
    if s.teacher_scheme:
        scheme_png=(ROOT/'torsion'/'assets'/f'scheme_{s.teacher_scheme:02}.png').read_bytes()
    else:
        scheme_png=_torsion_graph(calc)
    replace_png(d,'rId5',adapt_png(scheme_png,(247,115)))
    replace_png(d,'rId7',adapt_png(_torsion_graph(calc),(802,766)))
    d.save(output)
    return {'eight':eight,'Mmax':calc.max_T_knm,'diameters':dd}
