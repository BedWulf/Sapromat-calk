"""Единая точка запуска двух задач ОмГТУ, offline, Windows ONEFILE."""
from __future__ import annotations
import os,sys,json,subprocess,re,traceback
from pathlib import Path

BASE=Path(__file__).resolve().parent

def start_module(which):
    module=BASE/('tension' if which=='task1' else 'torsion')
    sys.path.insert(0,str(module))
    if which=='task1':
        from gui.main_window import main
        main()
    else:
        from torsion_gui import launch
        launch()

def launch():
    import tkinter as tk
    from tkinter import ttk,messagebox
    root=tk.Tk()
    root.title('ОмГТУ · Сопротивление материалов · Домашние задания')
    root.geometry('820x570')
    root.minsize(700,520)
    root.configure(bg='#f4f6fa')
    style=ttk.Style(root)
    if 'clam' in style.theme_names():style.theme_use('clam')
    style.configure('TLabel',font=('Segoe UI',10),background='#f4f6fa')
    style.configure('TButton',font=('Segoe UI',12),padding=12)
    style.configure('Title.TLabel',font=('Segoe UI',19,'bold'),foreground='#153857')
    wrapper=ttk.Frame(root,padding=24);wrapper.pack(expand=True,fill='both')
    ttk.Label(wrapper,text='СОПРОТИВЛЕНИЕ МАТЕРИАЛОВ',style='Title.TLabel').pack(anchor='w',pady=(5,3))
    ttk.Label(wrapper,text='ОмГТУ · кафедра «Машиноведение» · задания №1 и №2').pack(anchor='w',pady=(0,18))
    fields=ttk.LabelFrame(wrapper,text='Единые данные титульного листа',padding=12)
    fields.pack(fill='x',pady=(0,14))
    defs=[('ФИО студента','student',''),('Группа','group',''),('Полный вариант (Х-Х-строка-схема)','variant','11-2-23-4'),
       ('Преподаватель','teacher','Онищук С.Ю.'),('Дата выполнения','date',''),('Год','year','2026')]
    variables={}
    for i,(text,key,default) in enumerate(defs):
        v=tk.StringVar(value=default);variables[key]=v
        ttk.Label(fields,text=text).grid(row=i,column=0,sticky='w',padx=6,pady=4)
        ttk.Entry(fields,textvariable=v,width=46).grid(row=i,column=1,sticky='ew',padx=10,pady=4)
    fields.columnconfigure(1,weight=1)
    ttk.Label(wrapper,text='Выберите задачу. Исходные варианты и схемы можно изменить внутри неё.').pack(anchor='w',pady=(5,10))
    buttons=ttk.Frame(wrapper);buttons.pack(fill='x',pady=(0,10))
    def open_task(which):
        info={k:v.get().strip() for k,v in variables.items()}
        if info['variant'] and not re.fullmatch(r'\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+',info['variant']):
            if not messagebox.askyesno('Проверка варианта','Номер варианта обычно состоит из четырёх чисел. Продолжить?'):return
        env=dict(os.environ)
        env['OMGTU_TITLE_JSON']=json.dumps(info,ensure_ascii=False)
        # Один и тот же EXE служит главному окну и двум модулям.
        cmd=[sys.executable,'--'+which] if getattr(sys,'frozen',False) else [sys.executable,str(BASE/'main.py'),'--'+which]
        root.withdraw()
        try:
            proc=subprocess.run(cmd,env=env,cwd=str(BASE))
            if proc.returncode:messagebox.showwarning('Запуск модуля',f'Модуль завершился с кодом {proc.returncode}.')
        except Exception as exc:messagebox.showerror('Ошибка запуска',str(exc))
        finally:root.deiconify()
    ttk.Button(buttons,text='№1  Растяжение–сжатие',command=lambda:open_task('task1')).pack(side='left',expand=True,fill='x',padx=(0,7))
    ttk.Button(buttons,text='№2  Кручение',command=lambda:open_task('task2')).pack(side='left',expand=True,fill='x',padx=(7,0))
    ttk.Label(wrapper,text='Отчёты создаются на основе оригинальных файлов преподавателя.\nПрограмма работает без интернета; задачи №3 и №4 можно добавить позже.',justify='left').pack(anchor='w',pady=10)
    root.mainloop()

def self_check():
    # Тест на создание ДОКУМЕНТОВ, математическую модель, графики и ресурсы.
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        sys.path.insert(0,str(BASE/'torsion'))
        from teacher import example_teacher,teacher_settings
        from model import Calculation
        from teacher_exact import create_torsion_docx,create_tension_docx
        for s in (example_teacher(),teacher_settings(23,4)):
            create_torsion_docx(Path(temp)/'torsion.docx',Calculation(s),{'variant':'11-2-23-4'})
        sys.path.insert(0,str(BASE/'tension'))
        from core.variants import get_preset_scheme
        fixed,scheme=get_preset_scheme(22,1)
        create_tension_docx(Path(temp)/'tension.docx',scheme,{'P':15,'q':15,'l':1,'sigma_allow':160e6,'E':200e9},{'variant':'11-2-23-4'},fixed)
    # В EXE при самопроверке проверяется и оконная система.
    import tkinter as tk
    root=tk.Tk();root.withdraw();root.update();root.destroy()
    print('SUCCESS: torsion, tension, original Word templates, PNG, Tk')

if __name__=='__main__':
    if '--task1' in sys.argv:start_module('task1')
    elif '--task2' in sys.argv:start_module('task2')
    elif '--self-check' in sys.argv:
        try:self_check()
        except Exception:traceback.print_exc();sys.exit(1)
    else:launch()
