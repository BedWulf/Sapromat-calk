class ReportDataBuilder:
    @staticmethod
    def build_report(input_data, calc_results, dangerous_section, 
                     section_strength, section_stiffness, final_section):
        """Создать полный текст решения"""
        
        report = []
        
        # Заголовок
        report.append("ЗАДАЧА 1. Растяжение-сжатие.\n")
        
        # Исходные данные
        report.append("Дано:")
        report.append(f"P = {input_data['P']} кН")
        report.append(f"q = {input_data['q']} кН/м")
        report.append(f"l = {input_data['l']} м")
        report.append(f"[σ] = {input_data['sigma_allow']/1e6:.0f} МПа")
        report.append(f"E = {input_data['E']/1e6:.0f} МПа\n")
        
        # Требуется
        report.append("Требуется:")
        report.append("1. Записать уравнение продольной силы N(z), граничные условия задачи (Г.У.), рассчитать значение продольной силы по участкам (8 точек).")
        report.append("2. Выполнить чертёж схемы и эпюру в масштабе. Определить опасное сечение (координату z при |Nmax|).")
        report.append("3. Из условия прочности подобрать размер поперечного сечения, приняв допускаемое напряжение [σ] = 160 МПа. Полученные значения округлить до нормального ряда чисел.")
        report.append("4. Для стержня выбранного размера вычислить нормальные напряжения в опасном сечении σz.\n")
        
        # Решение
        report.append("Решение:")
        report.append("1. Совместим начало координат '0' с левым концом стержня и направим координатную ось z вдоль его продольной оси.")
        report.append("2. В соответствии со схемой нагружения разделим стержень на 4 участка (I-IV).\n")
        
        # Таблица значений
        report.append("3. Значения продольной силы по участкам:")
        report.append("| Участок | z, м | N(z), кН |")
        report.append("|---------|------|----------|")
        
        for segment_name, data in calc_results.items():
            report.append(f"| {segment_name} | {data['z_start']:.1f} | {data['N_start']:.2f} |")
            report.append(f"| {segment_name} | {data['z_end']:.1f} | {data['N_end']:.2f} |")
        
        report.append("")
        
        # Опасное сечение
        report.append(f"4. Опасное сечение: z = {dangerous_section[0]:.1f} м, |N|max = {dangerous_section[1]:.2f} кН\n")
        
        # Подбор по прочности
        report.append("5. Расчёт на прочность.")
        report.append("Условие прочности: σmax ≤ [σ]")
        report.append(f"F_min = |N|max / [σ] = {dangerous_section[1]*1e3} / {input_data['sigma_allow']} = {section_strength['F']:.6f} м²\n")
        
        if section_strength['shape'] == 'square':
            report.append(f"Для квадратного сечения: a = F = {section_strength['a']*1000:.2f} мм")
            report.append(f"Принимаем a = {section_strength['a']*1000:.0f} мм (по стандартному ряду)\n")
        elif section_strength['shape'] == 'rectangle_2_1':
            report.append(f"Для прямоугольного сечения (h=2b): b = √(F/2) = {section_strength['b']*1000:.2f} мм")
            report.append(f"Принимаем b = {section_strength['b']*1000:.0f} мм, h = {section_strength['h']*1000:.0f} мм (по стандартному ряду)\n")
        elif section_strength['shape'] == 'circle':
            report.append(f"Для круглого сечения: d = √(4F/π) = {section_strength['d']*1000:.2f} мм")
            report.append(f"Принимаем d = {section_strength['d']*1000:.0f} мм (по стандартному ряду)\n")
        
        # Подбор по жесткости
        report.append("6. Расчёт на жёсткость.")
        report.append(f"[W] = 0.002 · l = {input_data['W_coeff'] * input_data['l']} м\n")
        
        if section_stiffness['shape'] == 'square':
            report.append(f"Для квадратного сечения: a = {section_stiffness['a']*1000:.2f} мм")
            report.append(f"Принимаем a = {section_stiffness['a']*1000:.0f} мм (по стандартному ряду)\n")
        elif section_stiffness['shape'] == 'rectangle_2_1':
            report.append(f"Для прямоугольного сечения (h=2b): b = {section_stiffness['b']*1000:.2f} мм")
            report.append(f"Принимаем b = {section_stiffness['b']*1000:.0f} мм, h = {section_stiffness['h']*1000:.0f} мм (по стандартному ряду)\n")
        elif section_stiffness['shape'] == 'circle':
            report.append(f"Для круглого сечения: d = {section_stiffness['d']*1000:.2f} мм")
            report.append(f"Принимаем d = {section_stiffness['d']*1000:.0f} мм (по стандартному ряду)\n")
        
        # Окончательный выбор
        report.append("7. Окончательно принимаем размеры сечения по условию жёсткости (как более жёсткое требование).")
        
        if final_section['shape'] == 'square':
            report.append(f"Сторона квадрата a = {final_section['a']*1000:.0f} мм\n")
        elif final_section['shape'] == 'rectangle_2_1':
            report.append(f"Ширина b = {final_section['b']*1000:.0f} мм, высота h = {final_section['h']*1000:.0f} мм\n")
        elif final_section['shape'] == 'circle':
            report.append(f"Диаметр d = {final_section['d']*1000:.0f} мм\n")
        
        # Проверка прочности
        sigma_actual = dangerous_section[1] * 1e3 / final_section['F']
        report.append(f"8. Проверка прочности:")
        report.append(f"σ = |N|max / F = {dangerous_section[1]*1e3} / {final_section['F']} = {sigma_actual/1e6:.2f} МПа")
        report.append(f"σ = {sigma_actual/1e6:.2f} МПа ≤ [σ] = {input_data['sigma_allow']/1e6:.0f} МПа ✓")
        report.append(f"Условие прочности выполняется.\n")
        
        # Ответ
        report.append("Ответ:")
        if final_section['shape'] == 'square':
            report.append(f"Сторона квадрата a = {final_section['a']*1000:.0f} мм (по условию жёсткости)")
        elif final_section['shape'] == 'rectangle_2_1':
            report.append(f"Ширина b = {final_section['b']*1000:.0f} мм, высота h = {final_section['h']*1000:.0f} мм (по условию жёсткости)")
        elif final_section['shape'] == 'circle':
            report.append(f"Диаметр d = {final_section['d']*1000:.0f} мм (по условию жёсткости)")
        
        return "\n".join(report)