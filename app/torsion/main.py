"""main.py: GUI by default, self-test for Windows one-file deployment."""
import sys
import traceback
from pathlib import Path

def self_check(log_path=None):
    output=[]
    try:
        import tempfile
        from model import Calculation,demo_distributed,demo_simple
        from plotter import png_bytes
        from teacher_report import create_report
        from teacher import teacher_settings,example_teacher,strength_design
        for case in (demo_simple(),demo_distributed(),example_teacher(),teacher_settings(23,4)):
            c=Calculation(case)
            assert png_bytes(c)[:8]==b'\x89PNG\r\n\x1a\n'
            with tempfile.TemporaryDirectory() as tmp:
                f=str(Path(tmp)/'test.docx')
                create_report(c,f)
                assert Path(f).stat().st_size>15_000
        # Tk runtime check: able to initialize native window system.
        import tkinter as tk
        root=tk.Tk();root.withdraw();root.update();root.destroy()
        output.append('SUCCESS: mechanics, teachers variants, plots, Word export, Tk runtime')
        status=0
    except Exception:
        output.append(traceback.format_exc());status=1
    if log_path:
        Path(log_path).write_text('\n'.join(output),encoding='utf-8')
    else:
        print('\n'.join(output))
    return status

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--self-check':
        sys.exit(self_check(sys.argv[2] if len(sys.argv)>2 else None))
    from torsion_gui import launch
    launch()
