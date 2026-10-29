#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_calculator():
    from core.rod import Rod
    from core.loads import ConcentratedForce, DistributedLoad, Direction
    from core.calculator import Calculator
    
    rod = Rod(total_length=4.0, n_segments=4)
    rod.set_boundary(left=-8.0)
    
    rod.add_load(DistributedLoad(
        start=1.0, end=2.0, intensity=40.0, direction=Direction.POSITIVE
    ))
    
    rod.add_load(ConcentratedForce(
        start=3.0, magnitude=20.0, direction=Direction.NEGATIVE
    ))
    
    calc = Calculator(rod)
    
    print("=== Расчёт продольной силы N(z) ===")
    results = calc.compute_at_boundaries()
    
    for segment, data in results.items():
        print(f"{segment}: z={data['z_start']:.1f}м, N={data['N_start']:.2f} кН")
        print(f"         z={data['z_end']:.1f}м, N={data['N_end']:.2f} кН")
    
    dangerous_z, N_max = calc.find_dangerous_section()
    print(f"\nОпасное сечение: z={dangerous_z:.1f}м, |N|max={N_max:.2f} кН")
    
    from core.section import SectionSelector
    section = SectionSelector.from_strength(N_max, 160e6, "square")
    print(f"\nПодбор по прочности (квадрат): a={section['a']*1000:.2f} мм")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_calculator()
    else:
        from gui.main_window import main as gui_main
        gui_main()