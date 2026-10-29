"""Графический интерфейс Windows без серверов, браузера и подключения к сети."""
import io
import math
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from model import Settings,Calculation,demo_simple,demo_distributed
from teacher import teacher_settings, example_teacher, DATA, SCHEMES, strength_design
from plotter import png_bytes,save_plot
from teacher_report import create_report
from report import fnum


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Сопротивление материалов — Кручение четырёхучастного вала')
        self.geometry('1280x840')
        self.minsize(980,650)
        self.configure(bg='#eff4f9')
        self.calc=None
        self._img=None
        self.sv={}
        self._style()
        self._layout()
        # Идентичные данные титульного листа для обеих работ.
        import re,json
        try: common=json.loads(os.environ.get('OMGTU_TITLE_JSON','{}'))
        except Exception: common={}
        v=common.get('variant','')
        match=re.fullmatch(r'\s*\d+\s*-\s*\d+\s*-\s*(\d+)\s*-\s*(\d+)\s*',v)
        row,scheme=(23,4)
        if match:
            rr,ss=map(int,match.groups())
            if 1<=rr<=30 and 1<=ss<=30:row,scheme=rr,ss
        s=teacher_settings(row,scheme)
        for attr,key in [('title_student','student'),('title_group','group'),('title_teacher','teacher'),('title_year','year'),('title_date','date'),('title_variant','variant')]:
            if common.get(key):setattr(s,attr,common[key])
        self.load_settings(s)
        self.after(50,self.calculate)

    def _style(self):
        style=ttk.Style(self)
        if 'clam' in style.theme_names():style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10))
        style.configure('TFrame',background='#eff4f9')
        style.configure('TLabel',background='#eff4f9',foreground='#243952')
        style.configure('TLabelFrame',background='#eff4f9')
        style.configure('TLabelFrame.Label',background='#eff4f9',foreground='#153551',font=('Segoe UI',10,'bold'))
        style.configure('TNotebook',background='#eff4f9',borderwidth=0)
        style.configure('TNotebook.Tab',padding=(15,9))
        style.configure('Primary.TButton',padding=(14,8),font=('Segoe UI',10,'bold'))
        style.configure('TButton',padding=(8,6))
        style.configure('TEntry',padding=(5,5))
        style.configure('TCombobox',padding=(4,4))
        style.configure('Treeview',rowheight=27)
        style.configure('Treeview.Heading',font=('Segoe UI',9,'bold'))

    def _layout(self):
        head=ttk.Frame(self)
        head.pack(fill='x',padx=18,pady=(12,8))
        ttk.Label(head,text='КРУЧЕНИЕ • 4 УЧАСТКА',font=('Segoe UI',17,'bold'),foreground='#173957').pack(side='left')
        buttons=ttk.Frame(head);buttons.pack(side='right')
        ttk.Button(buttons,text='Пример преподавателя',command=lambda:self.load_settings(example_teacher())).pack(side='left',padx=3)
        ttk.Button(buttons,text='Вариант 23–4',command=lambda:self.load_settings(teacher_settings(23,4))).pack(side='left',padx=3)
        ttk.Button(buttons,text='Пример А',command=lambda:self.load_settings(demo_simple())).pack(side='left',padx=3)
        ttk.Button(buttons,text='Пример Б',command=lambda:self.load_settings(demo_distributed())).pack(side='left',padx=3)
        ttk.Button(buttons,text='Открыть JSON',command=self.open_json).pack(side='left',padx=3)
        ttk.Button(buttons,text='Сохранить JSON',command=self.save_json).pack(side='left',padx=3)
        self.tabs=ttk.Notebook(self)
        self.tabs.pack(fill='both',expand=True,padx=16,pady=(0,8))
        self.tab_inputs=ttk.Frame(self.tabs)
        self.tab_results=ttk.Frame(self.tabs)
        self.tab_title=ttk.Frame(self.tabs)
        self.tabs.add(self.tab_inputs,text='1. Исходные данные')
        self.tabs.add(self.tab_results,text='2. Результаты и эпюры')
        self.tabs.add(self.tab_title,text='3. Титульный лист')
        self._make_inputs();self._make_results();self._make_title()
        foot=ttk.Frame(self);foot.pack(fill='x',padx=16,pady=(2,12))
        ttk.Button(foot,text='РАССЧИТАТЬ',style='Primary.TButton',command=self.calculate).pack(side='left',padx=(0,8))
        ttk.Button(foot,text='Подобрать диаметры и подставить',command=self.apply_diameters).pack(side='left',padx=(0,8))
        ttk.Button(foot,text='Сохранить Word (.docx)',command=self.export_word).pack(side='left',padx=(0,8))
        ttk.Button(foot,text='Сохранить эпюры (.png)',command=self.export_png).pack(side='left')
        self.status=tk.StringVar(value='Готово: вводите данные и нажимайте «Рассчитать».')
        ttk.Label(foot,textvariable=self.status,wraplength=400).pack(side='right')

    def _inputvar(self,key,value=''):
        v=tk.StringVar(self,value=str(value));self.sv[key]=v;return v

    def _number_entry(self,parent,key,width=12):
        return ttk.Entry(parent,width=width,textvariable=self._inputvar(key))

    def _make_inputs(self):
        canvas=tk.Canvas(self.tab_inputs,highlightthickness=0,bg='#eff4f9')
        scroll=ttk.Scrollbar(self.tab_inputs,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        frm=ttk.Frame(canvas)
        cid=canvas.create_window((18,12),window=frm,anchor='nw')
        frm.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(cid,width=max(650,e.width-35)))
        canvas.bind('<Enter>',lambda e:canvas.bind_all('<MouseWheel>',lambda ev:canvas.yview_scroll(int(-ev.delta/120),'units')))
        canvas.bind('<Leave>',lambda e:canvas.unbind_all('<MouseWheel>'))
        selection=ttk.LabelFrame(frm,text='Варианты преподавателя из приложения 1 и 2',padding=14)
        selection.pack(fill='x',pady=(0,11))
        self.teacher_mode=tk.BooleanVar(value=True)
        ttk.Radiobutton(selection,text='Выбрать вариант преподавателя',variable=self.teacher_mode,value=True,command=self._mode_changed).grid(row=0,column=0,columnspan=3,sticky='w',padx=6,pady=5)
        ttk.Radiobutton(selection,text='Своя схема и свои нагрузки',variable=self.teacher_mode,value=False,command=self._mode_changed).grid(row=1,column=0,columnspan=3,sticky='w',padx=6,pady=5)
        ttk.Label(selection,text='№ строки исходных данных:').grid(row=2,column=0,sticky='w',padx=7,pady=5)
        self.row_var=tk.StringVar(value='23')
        self.row_cb=ttk.Combobox(selection,textvariable=self.row_var,values=[str(v) for v in DATA],state='readonly',width=8)
        self.row_cb.grid(row=2,column=1,sticky='w',padx=7)
        ttk.Label(selection,text='№ схемы нагружения:').grid(row=3,column=0,sticky='w',padx=7,pady=5)
        self.scheme_var=tk.StringVar(value='4')
        self.scheme_cb=ttk.Combobox(selection,textvariable=self.scheme_var,values=[str(v) for v in SCHEMES],state='readonly',width=8)
        self.scheme_cb.grid(row=3,column=1,sticky='w',padx=7)
        self.row_cb.bind('<<ComboboxSelected>>',self._apply_teacher_scheme)
        self.scheme_cb.bind('<<ComboboxSelected>>',self._apply_teacher_scheme)
        self.teacher_info=ttk.Label(selection,text='Схема из методички отображается справа.',foreground='#416883')
        self.teacher_info.grid(row=4,column=0,columnspan=3,sticky='w',padx=7,pady=4)
        self.teacher_scheme_preview=tk.Label(selection,bg='white',text='Выберите схему',width=36,height=7)
        self.teacher_scheme_preview.grid(row=0,column=3,rowspan=5,padx=12,pady=3,sticky='e')
        selection.columnconfigure(3,weight=1)
        general=ttk.LabelFrame(frm,text='Закрепление, материал и критерии прочности/жёсткости',padding=14)
        general.pack(fill='x',pady=(0,11))
        general.columnconfigure(1,weight=1);general.columnconfigure(3,weight=1)
        ttk.Label(general,text='Закрепление:').grid(row=0,column=0,sticky='w',padx=4,pady=5)
        self.fixed=tk.StringVar(value='left')
        self.fixed_cb=ttk.Combobox(general,textvariable=self.fixed,values=['left','right'],state='readonly',width=18)
        self.fixed_cb.grid(row=0,column=1,sticky='w',padx=4,pady=5)
        ttk.Label(general,text='left = слева; right = справа',foreground='#567089').grid(row=0,column=2,columnspan=2,sticky='w',padx=6)
        fields=[('G, МПа','G_MPa'),('[τ], МПа','tau_allow_MPa'),('[θ], рад/м','theta_allow_rad_m')]
        for i,(label,key) in enumerate(fields):
            col=0 if i!=1 else 2
            row=1 if i!=2 else 2
            ttk.Label(general,text=label).grid(row=row,column=col,sticky='w',padx=4,pady=4)
            self._number_entry(general,key).grid(row=row,column=col+1,sticky='w',padx=4,pady=4)
        ttk.Label(general,text='Для стали обычно G≈80000 МПа. [τ] и [θ] задайте по конкретному заданию.',foreground='#567089').grid(row=3,column=0,columnspan=4,sticky='w',padx=4,pady=7)
        seg=ttk.LabelFrame(frm,text='Четыре участка: размеры и распределённые крутящие моменты',padding=14)
        seg.pack(fill='x',pady=(0,11))
        seg.columnconfigure(6,weight=1)
        for j,t in enumerate(('№','Длина ℓ, м','m, кН·м/м','Наружный D, мм','k = dвн/D','Примечание')):
            ttk.Label(seg,text=t,font=('Segoe UI',9,'bold')).grid(row=0,column=j,padx=8,pady=(0,8),sticky='w')
        self.diameter_entries=[]
        self.own_load_entries=[]
        for i in range(4):
            ttk.Label(seg,text=f'{i+1}').grid(row=i+1,column=0,padx=8,pady=5)
            entry=self._number_entry(seg,f'L{i}',10);entry.grid(row=i+1,column=1,padx=8,pady=5);self.own_load_entries.append(entry)
            entry=self._number_entry(seg,f'q{i}',13);entry.grid(row=i+1,column=2,padx=8,pady=5);self.own_load_entries.append(entry)
            di=self._number_entry(seg,f'D{i}',13)
            di.grid(row=i+1,column=3,padx=8,pady=5);self.diameter_entries.append(di)
            self._number_entry(seg,f'k{i}',12).grid(row=i+1,column=4,padx=8,pady=5)
            ttk.Label(seg,text='0 — сплошной; 0,5 — труба').grid(row=i+1,column=5,padx=8,pady=5,sticky='w')
        self.common=tk.BooleanVar(value=False)
        ttk.Checkbutton(seg,text='Один наружный диаметр D на всех четырёх участках (берётся поле участка 1)',variable=self.common,command=self._update_common).grid(row=5,column=0,columnspan=6,sticky='w',padx=7,pady=(10,0))
        loads=ttk.LabelFrame(frm,text='Пять узлов: сосредоточенные крутящие моменты Mᵢ',padding=14)
        loads.pack(fill='x',pady=(0,11))
        for i in range(5):
            ttk.Label(loads,text=f'M{i}, кН·м').grid(row=0,column=i,padx=13,pady=5)
            entry=self._number_entry(loads,f'M{i}',12);entry.grid(row=1,column=i,padx=13,pady=5);self.own_load_entries.append(entry)
        ttk.Label(loads,text='Положительное направление — правило правого винта вокруг оси +z. Нагрузки разрешено задавать на обоих торцах, включая заделку.',foreground='#567089').grid(row=2,column=0,columnspan=5,sticky='w',pady=9,padx=8)
        box=ttk.LabelFrame(frm,text='Граничные условия (автоматически)',padding=12)
        box.pack(fill='x',pady=(0,11))
        ttk.Label(box,text='При левой заделке φ(0)=0, при правой φ(L)=0. Вторая величина вычисляется интегрированием Mк/(GJp). Реакция заделки вычисляется по ΣM=0.').pack(anchor='w',padx=4,pady=3)
        ttk.Label(box,text='Вводить Mк(0) и Mк(4l) не нужно. Условие на свободном конце известно по схеме, второе вычисляется автоматически.',foreground='#476d86').pack(anchor='w',padx=4,pady=3)
        ttk.Label(box,text='Для стандартного варианта L и m, закрепление и нагрузки выставляются из методички автоматически.',foreground='#476d86').pack(anchor='w',padx=4,pady=3)

    def _make_title(self):
        f=ttk.LabelFrame(self.tab_title,text='Поля титульного листа (оформление по логике образца ОмГТУ)',padding=20)
        f.pack(fill='x',padx=30,pady=23)
        labels=[('ФИО студента','title_student'),('Группа','title_group'),('Преподаватель','title_teacher'),('Вариант / название','title_variant'),('Год','title_year'),('Дата','title_date'),('Название работы','title_task')]
        for i,(label,key) in enumerate(labels):
            ttk.Label(f,text=label,width=25).grid(row=i,column=0,sticky='w',padx=8,pady=8)
            ttk.Entry(f,textvariable=self._inputvar(key),width=61).grid(row=i,column=1,sticky='ew',padx=8,pady=8)
        ttk.Label(f,text='Подстановка этих данных в Word не меняет результаты расчёта.',foreground='#567089').grid(row=len(labels),column=0,columnspan=2,sticky='w',padx=8,pady=15)

    def _make_results(self):
        top=ttk.Frame(self.tab_results);top.pack(fill='both',expand=True,padx=10,pady=10)
        left=ttk.Frame(top);left.pack(side='left',fill='both',expand=False)
        self.results=tk.Text(left,wrap='word',width=43,font=('Consolas',10),relief='flat',padx=12,pady=10,bg='#fff',fg='#1b314b')
        results_scroll=ttk.Scrollbar(left,orient='vertical',command=self.results.yview)
        self.results.configure(yscrollcommand=results_scroll.set)
        results_scroll.pack(side='right',fill='y')
        self.results.pack(side='left',fill='both',expand=True)
        frame=ttk.Frame(top);frame.pack(side='right',fill='both',expand=True,padx=(12,0))
        self.preview=tk.Label(frame,text='Здесь появится схема с эпюрами',bg='white',fg='#526f89')
        self.preview.pack(fill='both',expand=True)
        self.preview.bind('<Configure>',self._resize_image)

    def _update_common(self):
        for i,e in enumerate(self.diameter_entries):
            e.configure(state='disabled' if (i>0 and self.common.get()) else 'normal')

    def _preview_scheme(self):
        try:
            path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'assets',f'scheme_{int(self.scheme_var.get()):02}.png')
            image=Image.open(path).convert('RGB')
            image.thumbnail((285,140),Image.Resampling.LANCZOS)
            self._teacher_photo=ImageTk.PhotoImage(image)
            self.teacher_scheme_preview.configure(image=self._teacher_photo,text='',width=image.width,height=image.height)
        except Exception:
            self.teacher_scheme_preview.configure(text='Изображение недоступно',image='')

    def _mode_changed(self):
        teacher=self.teacher_mode.get()
        self.row_cb.configure(state='readonly' if teacher else 'disabled')
        self.scheme_cb.configure(state='readonly' if teacher else 'disabled')
        self.fixed_cb.configure(state='disabled' if teacher else 'readonly')
        for e in self.own_load_entries:e.configure(state='disabled' if teacher else 'normal')
        if teacher:self._apply_teacher_scheme()
        else:
            self.teacher_info.configure(text='Свои нагрузки и закрепление: редактируйте поля ниже.')
            self.teacher_scheme_preview.configure(image='',text='Ручная схема')

    def _apply_teacher_scheme(self,event=None):
        if not self.teacher_mode.get():return
        row=int(self.row_var.get());scheme=int(self.scheme_var.get())
        old=self.sv['title_variant'].get() if 'title_variant' in self.sv else ''
        s=teacher_settings(row,scheme)
        self.fixed.set(s.fixed)
        for i in range(4):
            self.sv[f'L{i}'].set(str(s.lengths_m[i]))
            self.sv[f'q{i}'].set(str(s.distributed_knm_per_m[i]))
        for i in range(5):self.sv[f'M{i}'].set(str(s.node_moments_knm[i]))
        # В полном варианте первые два числа относятся к задаче №3.
        parts=old.split('-')
        prefix='-'.join(parts[:2]) if len(parts)==4 else 'Х-Х'
        self.sv['title_variant'].set(f'{prefix}-{row}-{scheme}')
        self.sv['tau_allow_MPa'].set('90')
        L,m=DATA[row]
        self.teacher_info.configure(text=f'Строка {row}: L = {L:g} кН·м, m = {m:g} кН·м/м; заделка: {"слева" if s.fixed=="left" else "справа"}.')
        self._preview_scheme()
        self.status.set('Стандартный вариант выбран. Нажмите «Рассчитать».')

    def load_settings(self,s:Settings):
        if s.teacher_data_row and s.teacher_scheme:
            s=teacher_settings(s.teacher_data_row,s.teacher_scheme,s)
        self.teacher_mode.set(bool(s.teacher_data_row and s.teacher_scheme))
        if self.teacher_mode.get():
            self.row_var.set(str(s.teacher_data_row));self.scheme_var.set(str(s.teacher_scheme))
        self.fixed.set(s.fixed)
        for key in ('G_MPa','tau_allow_MPa','theta_allow_rad_m','title_student','title_group','title_teacher','title_variant','title_year','title_date','title_task'):
            self.sv[key].set(str(getattr(s,key)))
        for i in range(4):
            for key,value in [('L',s.lengths_m[i]),('q',s.distributed_knm_per_m[i]),('D',s.diameter_mm[i]),('k',s.hole_ratio[i])]:
                self.sv[f'{key}{i}'].set(str(value))
        for i in range(5):self.sv[f'M{i}'].set(str(s.node_moments_knm[i]))
        self.common.set(False);self._update_common()
        self._mode_changed()
        if s.teacher_data_row and s.teacher_scheme:
            self.sv['title_variant'].set(s.title_variant)
        self.status.set('Данные загружены; нажмите «Рассчитать».')
        self.tabs.select(self.tab_inputs)

    @staticmethod
    def _parse_number(v,label):
        try: result=float(v.strip().replace(' ','').replace(',','.'))
        except Exception as e: raise ValueError(f'{label}: введите число') from e
        if not math.isfinite(result):raise ValueError(f'{label}: требуется конечное число')
        return result

    def settings(self):
        def num(k):return self._parse_number(self.sv[k].get(),k)
        d=[num(f'D{i}') for i in range(4)]
        if self.common.get():d=[d[0]]*4
        s=Settings(lengths_m=[num(f'L{i}') for i in range(4)],
                   node_moments_knm=[num(f'M{i}') for i in range(5)],
                   distributed_knm_per_m=[num(f'q{i}') for i in range(4)],
                   diameter_mm=d,hole_ratio=[num(f'k{i}') for i in range(4)],
                   fixed=self.fixed.get(),G_MPa=num('G_MPa'),tau_allow_MPa=num('tau_allow_MPa'),theta_allow_rad_m=num('theta_allow_rad_m'),
                   teacher_data_row=int(self.row_var.get()) if self.teacher_mode.get() else 0,
                   teacher_scheme=int(self.scheme_var.get()) if self.teacher_mode.get() else 0,
                   **{k:self.sv[k].get().strip() for k in ('title_student','title_group','title_teacher','title_variant','title_year','title_date','title_task')})
        s.validate()
        if self.teacher_mode.get():
            expected=teacher_settings(s.teacher_data_row,s.teacher_scheme,s)
            s=expected
        return s

    def calculate(self):
        try:
            self.calc=Calculation(self.settings())
            c=self.calc;s=c.s
            design=strength_design(c)
            lines=['РЕЗУЛЬТАТЫ РАСЧЁТА','='*33,'','Закрепление: '+('слева' if s.fixed=='left' else 'справа'),f'Длина L: {fnum(c.coords[-1])} м',f'Реакция M_R: {fnum(c.reaction_knm)} кН·м','',
                   'ЭПЮРА Мк(z), кН·м','Участок | слева  | справа']
            for i in range(4): lines.append(f'   {i+1}    | {c.start_T[i]:+7.3f} | {c.end_T[i]:+7.3f}')
            lines.extend(['',f'|Mк|max = {fnum(c.max_T_knm)} кН·м',f'τmax = {fnum(c.max_tau_MPa)} МПа',f'[τ] = {fnum(s.tau_allow_MPa)} МПа',f'Прочность: {"ВЫПОЛНЯЕТСЯ" if c.max_tau_MPa <= s.tau_allow_MPa + 1e-8 else "НЕ ВЫПОЛНЯЕТСЯ"}', '',
                          f'θmax = {fnum(c.max_theta_rad_m,6)} рад/м',f'[θ] = {fnum(s.theta_allow_rad_m,6)} рад/м',f'Жёсткость: {"ВЫПОЛНЯЕТСЯ" if c.max_theta_rad_m <= s.theta_allow_rad_m + 1e-9 else "НЕ ВЫПОЛНЯЕТСЯ"}', '',
                          f'max |φ| = {fnum(c.max_phi_rad*180/math.pi)}°','',
                          'УГЛЫ НА УЗЛАХ (град):'])
            for i,v in enumerate(c.phi_nodes): lines.append(f'  z={c.coords[i]:6.3f}: {v*180/math.pi:+9.4f}°')
            lines.extend(['','ПОДБОР D ПО ОБОИМ УСЛОВИЯМ','Участок | Dтр → Dнорм, мм'])
            for i in range(4): lines.append(f'   {i+1}    | {c.required_d[i]:7.2f} → {c.recommended_d[i]:.0f}')
            lines.append('\nЗначения D вводятся пользователем;')
            lines.append('рекомендации НЕ заменяют их автоматически.')
            lines.extend(['','ПО ТРЕБОВАНИЯМ ПРЕПОДАВАТЕЛЯ:',
                f'Круглый d = {design["d_round"]} мм',
                f'Кольцевой D/d = {design["D_hollow"]}/{design["d_hollow"]:g} мм',
                f'Экономия веса ≈ {fnum(design["weight_saved_pct"])} %'])
            self.results.configure(state='normal');self.results.delete('1.0','end');self.results.insert('1.0','\n'.join(lines));self.results.configure(state='disabled')
            self._png=png_bytes(c);self._resize_image()
            self.status.set('Расчёт выполнен. Проверены равновесие и условие закрепления.')
            self.tabs.select(self.tab_results)
            return c
        except Exception as exc:
            self.calc=None
            self.status.set('Ошибка ввода: '+str(exc))
            messagebox.showerror('Проверка исходных данных',str(exc))
            return None

    def _resize_image(self,event=None):
        if not getattr(self,'_png',None) or not hasattr(self,'preview'):return
        w=max(self.preview.winfo_width()-10,450)
        h=max(self.preview.winfo_height()-10,400)
        im=Image.open(io.BytesIO(self._png)).convert('RGB')
        im.thumbnail((w,h),Image.Resampling.LANCZOS)
        self._img=ImageTk.PhotoImage(im)
        self.preview.configure(image=self._img,text='')

    def apply_diameters(self):
        c=self.calculate()
        if c is None:return
        values=[max(c.recommended_d)]*4 if self.common.get() else c.recommended_d
        for i,value in enumerate(values):self.sv[f'D{i}'].set(str(int(value)))
        self.calculate()
        self.status.set('Рекомендуемые диаметры подставлены. Пересчитаны напряжения и углы.')

    def export_word(self):
        c=self.calculate()
        if c is None:return
        file=filedialog.asksaveasfilename(title='Сохранить отчёт Word',defaultextension='.docx',initialfile='Kruchenie_otchet.docx',filetypes=[('Документ Word','*.docx')])
        if not file:return
        try:
            from teacher_exact import create_torsion_docx
            create_torsion_docx(file,c,{
                'student':c.s.title_student, 'group':c.s.title_group,
                'variant':c.s.title_variant, 'teacher':c.s.title_teacher,
                'year':c.s.title_year, 'date':c.s.title_date,
                'position':'Ст. преп. каф.'})
            self.status.set('Отчёт сохранён: '+os.path.basename(file))
            messagebox.showinfo('Отчёт сохранён',file)
        except Exception as e:messagebox.showerror('Ошибка экспорта Word',str(e))

    def export_png(self):
        c=self.calculate()
        if c is None:return
        file=filedialog.asksaveasfilename(title='Сохранить эпюры',defaultextension='.png',initialfile='Kruchenie_epury.png',filetypes=[('Изображение PNG','*.png')])
        if file:
            try:save_plot(c,file);self.status.set('Эпюра сохранена: '+os.path.basename(file))
            except Exception as e:messagebox.showerror('Ошибка сохранения PNG',str(e))

    def save_json(self):
        try:s=self.settings()
        except Exception as e:messagebox.showerror('Ввод',str(e));return
        path=filedialog.asksaveasfilename(title='Сохранить вариант',defaultextension='.json',initialfile='variant.json',filetypes=[('Вариант JSON','*.json')])
        if path:
            with open(path,'w',encoding='utf-8') as f:f.write(s.to_json())
            self.status.set('Вариант сохранён в JSON')

    def open_json(self):
        path=filedialog.askopenfilename(title='Открыть вариант',filetypes=[('Вариант JSON','*.json')])
        if path:
            try:
                with open(path,'r',encoding='utf-8') as f:s=Settings.from_json(f.read())
                self.load_settings(s);self.calculate()
            except Exception as e:messagebox.showerror('Ошибка чтения варианта',str(e))


def launch():
    App().mainloop()
