"""Краткое текстовое резюме расчёта, совпадающее с числовой частью Word."""
import math

class ReportDataBuilder:
    @staticmethod
    def build_report(input_data, calc_results, dangerous_section,
                     section_strength, section_stiffness, final_section):
        P,q,l=input_data['P'],input_data['q'],input_data['l']
        sigma_allow=input_data['sigma_allow']
        z_max,n_max=dangerous_section
        f_min=n_max*1000/sigma_allow
        rows=['ЗАДАЧА 1. Растяжение–сжатие.',
              f'Дано: P={P:g} кН; q={q:g} кН/м; l={l:g} м; '
              f'[σ]={sigma_allow/1e6:g} МПа.',
              'N>0 — растяжение; N<0 — сжатие.',
              'Граничные значения по участкам (слева направо):']
        for number,values in enumerate(calc_results.values(),1):
            rows.append(f"{number}: z={values['z_start']:g} м, N={values['N_start']:.3f} кН; "
                        f"z={values['z_end']:g} м, N={values['N_end']:.3f} кН")
        rows.append(f'Опасное сечение: z={z_max:g} м, |N|max={n_max:.3f} кН.')
        rows.append(f'Fmin=|N|max/[σ]={f_min*1e6:.3f} мм².')
        if final_section['shape']=='rectangle_2_1':
            b_min=math.sqrt(f_min/2)*1000
            rows.append(f'Прямоугольник h=2b: bmin={b_min:.3f} мм; '
                        f"принято b={final_section['b']*1000:.0f} мм, "
                        f"h={final_section['h']*1000:.0f} мм.")
        elif final_section['shape']=='square':
            rows.append(f"Принято квадратное сечение a={final_section['a']*1000:.0f} мм.")
        else:
            rows.append(f"Принято круглое сечение d={final_section['d']*1000:.0f} мм.")
        if input_data.get('consider_stiffness',False):
            rows.append('Дополнительно учтено ограничение на осевое перемещение.')
        else:
            rows.append('Подбор выполнен по прочности, как в задаче №1 преподавателя.')
        sig_actual=n_max*1000/final_section['F']/1e6
        rows.append(f'Проверка: σmax={sig_actual:.3f} МПа ≤ {sigma_allow/1e6:g} МПа '
                    f"— {'выполнено' if sig_actual<=sigma_allow/1e6+1e-9 else 'НЕ выполнено'}.")
        return '\n'.join(rows)
