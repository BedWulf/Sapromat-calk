from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import os
import math


class WordExporter:
    def __init__(self):
        self.doc = Document()
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        for section in self.doc.sections:
            section.top_margin = Cm(2)
            section.bottom_margin = Cm(2)
            section.left_margin = Cm(2.5)
            section.right_margin = Cm(1.5)

    def _add_para(self, text, bold=False, italic=False, size=12, align=None, indent=None):
        p = self.doc.add_paragraph()
        if align:
            p.alignment = align
        if indent:
            p.paragraph_format.left_indent = Cm(indent)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(size)
        run.bold = bold
        run.italic = italic
        return p

    def _add_mixed(self, parts, indent=None):
        """parts: список (текст, bold, italic)"""
        p = self.doc.add_paragraph()
        if indent:
            p.paragraph_format.left_indent = Cm(indent)
        for text, bold, italic in parts:
            run = p.add_run(text)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)
            run.bold = bold
            run.italic = italic
        return p

    # =========================================================
    # ТИТУЛЬНЫЙ ЛИСТ
    # =========================================================
    def create_title_page(self, title_data):
        self.doc.add_paragraph()
        self.doc.add_paragraph()
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for line in [
            "Министерство науки и высшего образования РФ",
            "ФГАОУ ВО «Омский государственный технический университет»",
            "Кафедра «Машиноведение»"
        ]:
            run = p.add_run(line + "\n")
            run.font.size = Pt(12)
            run.font.name = 'Times New Roman'

        self.doc.add_paragraph()
        self.doc.add_paragraph()

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("ДОМАШНЕЕ ЗАДАНИЕ № 1\n")
        run.font.size = Pt(14); run.bold = True; run.font.name = 'Times New Roman'
        for line in [
            "по дисциплине\n",
            "«СОПРОТИВЛЕНИЕ МАТЕРИАЛОВ»\n",
            "за I семестр 2026/27 уч. года\n",
            "по теме «Растяжение-сжатие»"
        ]:
            run = p.add_run(line)
            run.font.size = Pt(12); run.font.name = 'Times New Roman'

        self.doc.add_paragraph()
        self.doc.add_paragraph()
        self.doc.add_paragraph()

        p = self.doc.add_paragraph()
        for line in [
            f"Вариант: {title_data.get('variant', '')}\n",
            f"Выполнил: ст. гр. {title_data.get('group', '')}\n",
            f"          {title_data.get('student_name', '')} __________\n",
            f"Дата: {title_data.get('date', '')}\n"
        ]:
            run = p.add_run(line)
            run.font.size = Pt(12); run.font.name = 'Times New Roman'

        self.doc.add_paragraph()
        p = self.doc.add_paragraph()
        for line in [
            f"Проверил: {title_data.get('teacher', '')} ___________\n",
            "Дата: __________"
        ]:
            run = p.add_run(line)
            run.font.size = Pt(12); run.font.name = 'Times New Roman'

        self.doc.add_paragraph()
        self.doc.add_paragraph()
        self.doc.add_paragraph()

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Омск – 2026")
        run.font.size = Pt(12); run.font.name = 'Times New Roman'

        self.doc.add_page_break()

    # =========================================================
    # ПОЛНЫЙ ТЕКСТ РАСЧЁТА
    # =========================================================
    def add_calculation_text(self, input_data, calc_results,
                             dangerous_section, section_strength,
                             section_stiffness, final_section,
                             scheme=None, boundary_conditions=None):
        P = input_data['P']
        q = input_data['q']
        l = input_data['l']
        sigma = input_data['sigma_allow'] / 1e6
        E = input_data['E'] / 1e6
        W_coeff = input_data['W_coeff']

        shape_names = {0: 'квадрат', 1: 'прямоугольник (h = 2b)', 2: 'круг'}
        shape = shape_names.get(input_data['shape'], 'квадрат')

        # ===== ЗАГОЛОВОК =====
        self._add_para("ЗАДАЧА 1. Растяжение – сжатие.", bold=True, size=14)

        # ===== ДАНО =====
        self._add_para("Дано:", bold=True)
        self._add_para(f"P = {P} кН")
        self._add_para(f"q = {q} кН/м")
        self._add_para(f"l = {l} м")
        self._add_para(f"[σ] = {sigma:.0f} МПа")
        self._add_para(f"E = {E:.0f} МПа")
        self._add_para(f"Форма сечения: {shape}")

        # ===== ТРЕБУЕТСЯ =====
        self._add_para("Требуется:", bold=True)
        self._add_para("1. Записать уравнение продольной силы N(z), граничные условия задачи (Г.У.), рассчитать значение продольной силы по участкам (8 точек).")
        self._add_para("2. Выполнить чертёж схемы и эпюру в масштабе. Определить опасное сечение (координату z при |N|max).")
        self._add_para("3. Из условия прочности подобрать размер поперечного сечения, приняв допускаемое напряжение [σ] = 160 МПа. Полученные значения округлить до нормального ряда чисел.")
        self._add_para("4. Для стержня выбранного размера вычислить нормальные напряжения в опасном сечении σz.")

        # ===== РЕШЕНИЕ =====
        self._add_para("Решение:", bold=True)

        # п.1
        self._add_mixed([
            ("1. ", True, False),
            ("Совместим начало координат «0» с левым концом стержня и направим координатную ось z вдоль его продольной оси, поставим отрезки в диапазоне от 0 до 4l с шагом в l.", False, False)
        ])

        # п.2
        self._add_mixed([
            ("2. ", True, False),
            ("В соответствии со схемой нагружения разделим стержень на 4 участка (I–IV).", False, False)
        ])

        # п.3 — универсальное уравнение
        self._add_mixed([
            ("3. ", True, False),
            ("Запишем уравнение продольных сил:", False, False)
        ])

        # Строим уравнение на основе схемы
        equation_text, segment_equations = self._build_equation(scheme, P, q, l, boundary_conditions)

        self._add_para(equation_text, indent=1)

        self._add_para(
            "Действующие на стержень распределённую нагрузку q и "
            "сосредоточенную силу P проецируем на ось 0z.",
            indent=1
        )

        # Пояснения по участкам
        self._write_segment_explanations(segment_equations, P, q, l)

        # п.4 — граничные условия
        self._add_mixed([
            ("4. ", True, False),
            ("Запишем граничные условия. Граничное условие (Г.У.) — это информация о величине продольной силы в начале и конце стержня.", False, False)
        ])

        N0 = boundary_conditions.get('N_left', 0) if boundary_conditions else 0
        N4l = boundary_conditions.get('N_right', 0) if boundary_conditions else 0

        if N0 is not None:
            self._add_para(f"Г.У.: N(0) = {N0:.2f} кН.", indent=1)
        else:
            self._add_para(f"Г.У.: N(4l) = {N4l:.2f} кН.", indent=1)

        # п.5 — раскрытие скобок
        self._add_mixed([
            ("5. ", True, False),
            ("Минус перед квадратными скобками [ ] говорит о природе действующих на стержень внутренних сил, которые равны по модулю, но противоположны по направлению приложенным к стержню внешним силам. Раскроем квадратные скобки:", False, False)
        ])

        expanded = self._build_expanded_equation(segment_equations, P, q, l, N0)
        self._add_para(expanded, indent=1)

        # п.6 — расчёт по участкам
        self._add_mixed([
            ("6. ", True, False),
            ("Построение графиков ведётся по участкам. Вместо z подставляем значения границ участков.", False, False)
        ])

        self._write_detailed_segment_calculations(calc_results, segment_equations, P, q, l, N0)

        # п.7 — таблица
        self._add_mixed([
            ("7. ", True, False),
            ("Запишем все значения в таблицу:", False, False)
        ])
        self._write_table(calc_results)

        # п.8 — опасное сечение
        z_dang, N_max = dangerous_section
        self._add_mixed([
            ("8. ", True, False),
            (f"По полученным значениям строим эпюру. Опасное сечение: z = {z_dang} м, |N|max = {N_max:.2f} кН.", False, False)
        ])

        # п.9 — расчёт на прочность
        self._add_mixed([
            ("9. ", True, False),
            ("Расчёт на прочность.", False, False)
        ])
        self._write_strength_calculation(input_data, N_max, section_strength, final_section)

        # п.10 — расчёт на жёсткость
        self._add_mixed([
            ("10. ", True, False),
            ("Расчёт на жёсткость.", False, False)
        ])
        self._write_stiffness_calculation(input_data, section_stiffness)

        # п.11 — окончательный выбор
        self._add_mixed([
            ("11. ", True, False),
            ("Окончательно принимаем размеры сечения по условию, дающему больший размер.", False, False)
        ])
        self._write_final_choice(final_section)

        # п.12 — проверка прочности
        self._add_mixed([
            ("12. ", True, False),
            ("Проверка прочности для выбранного сечения.", False, False)
        ])
        self._write_strength_check(input_data, N_max, final_section)

        # ===== ОТВЕТ =====
        self._add_mixed([
            ("Ответ: ", True, False),
        ])
        self._write_answer(final_section)

    # =========================================================
    # ПОСТРОЕНИЕ УРАВНЕНИЯ
    # =========================================================
    def _build_equation(self, scheme, P, q, l, boundary_conditions):
        """Строит символьное уравнение N(z) и уравнения по участкам"""
        # Собираем все нагрузки с их символическими именами
        loads_info = []  # (type, count, direction, position/start/end, symbol)
        force_counter = 0
        dist_counter = 0

        if scheme:
            for seg_idx, seg_loads in enumerate(scheme):
                for load in seg_loads:
                    count = load['count']
                    direction = load['direction']
                    if load['type'] == 'force':
                        force_counter += 1
                        symbol = f"{count}P" if count > 1 else "P"
                        loads_info.append({
                            'type': 'force',
                            'count': count,
                            'direction': direction,
                            'position': load['position'],
                            'segment': seg_idx + 1,
                            'symbol': symbol,
                            'value': count * P
                        })
                    elif load['type'] == 'distributed':
                        dist_counter += 1
                        symbol = f"{count}q" if count > 1 else "q"
                        loads_info.append({
                            'type': 'distributed',
                            'count': count,
                            'direction': direction,
                            'start': load['start'],
                            'end': load['end'],
                            'segment': seg_idx + 1,
                            'symbol': symbol,
                            'value': count * q
                        })

        # Строим уравнение N(z) = N(0) - [ ... ]
        # В скобках: для каждой нагрузки её вклад
        # Сила P в точке a: direction * symbol * <z-a>^0
        # Нагрузка q от a до b: direction * symbol * <z-a>^1 - direction * symbol * <z-b>^1

        terms = []
        for load in loads_info:
            if load['type'] == 'force':
                a = load['position']
                a_str = self._coord_to_str(a, l)
                sign = "+" if load['direction'] == 1 else "-"
                terms.append(f"{sign} {load['symbol']}·‹z − {a_str}›⁰")
            elif load['type'] == 'distributed':
                a = load['start']
                b = load['end']
                a_str = self._coord_to_str(a, l)
                b_str = self._coord_to_str(b, l)
                sign_start = "+" if load['direction'] == 1 else "-"
                sign_end = "-" if load['direction'] == 1 else "+"
                terms.append(f"{sign_start} {load['symbol']}·(z − {a_str})")
                terms.append(f"{sign_end} {load['symbol']}·(z − {b_str})")

        # Собираем уравнение
        if terms:
            inner = " ".join(terms)
            equation = f"N(z) = N(0) − [ {inner} ]"
        else:
            equation = "N(z) = N(0)"

        # Строим уравнения по участкам
        segment_equations = {1: [], 2: [], 3: [], 4: []}
        for load in loads_info:
            seg = load['segment']
            # Нагрузка действует на участках >= seg
            for s in range(seg, 5):
                if load['type'] == 'force':
                    segment_equations[s].append({
                        'type': 'force',
                        'symbol': load['symbol'],
                        'direction': load['direction'],
                        'position': load['position'],
                        'value': load['value']
                    })
                elif load['type'] == 'distributed':
                    segment_equations[s].append({
                        'type': 'distributed_start',
                        'symbol': load['symbol'],
                        'direction': load['direction'],
                        'start': load['start'],
                        'value': load['value']
                    })
                    segment_equations[s].append({
                        'type': 'distributed_end',
                        'symbol': load['symbol'],
                        'direction': load['direction'],
                        'end': load['end'],
                        'value': load['value']
                    })

        return equation, segment_equations

    def _coord_to_str(self, coord, l):
        """Преобразует координату в строку вида 'l', '2l', '3l', '4l'"""
        if abs(coord) < 0.01:
            return "0"
        ratio = coord / l
        if abs(ratio - round(ratio)) < 0.01:
            n = int(round(ratio))
            if n == 1:
                return "l"
            return f"{n}l"
        return f"{coord:.2f}"

    def _write_segment_explanations(self, segment_equations, P, q, l):
        """Пояснения по каждому участку как в методичке"""
        seg_names = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}

        for seg_num in range(1, 5):
            loads = segment_equations.get(seg_num, [])
            seg_name = seg_names[seg_num]

            if not loads:
                self._add_para(
                    f"{seg_name}. На {seg_name.lower()} участке мысленно закрываем всё, что расположено справа от черты S, "
                    f"никаких нагрузок на участке нет. Получаем 0{seg_name}.",
                    indent=1
                )
            else:
                # Группируем нагрузки по типу
                forces = [ld for ld in loads if ld['type'] == 'force']
                dist_starts = [ld for ld in loads if ld['type'] == 'distributed_start']
                dist_ends = [ld for ld in loads if ld['type'] == 'distributed_end']

                parts = []

                for fs in forces:
                    direction_str = "сонаправлена оси 0z" if fs['direction'] == 1 else "направлена против оси 0z"
                    sign = "+" if fs['direction'] == 1 else "−"
                    parts.append(
                        f"На {seg_name.lower()} участке действует сосредоточенная сила {fs['symbol']}={fs['value']} кН, {direction_str}. "
                        f"Поэтому записываем: {sign} {fs['symbol']}{seg_name}."
                    )

                for ds in dist_starts:
                    direction_str = "сонаправлена оси 0z" if ds['direction'] == 1 else "направлена против оси 0z"
                    sign = "+" if ds['direction'] == 1 else "−"
                    parts.append(
                        f"На {seg_name.lower()} участке действует распределённая нагрузка {ds['symbol']}={ds['value']} кН/м, {direction_str}. "
                        f"Продольная сила от этой нагрузки равняется произведению её величины на длину участка. "
                        f"Поэтому записываем: {sign} {ds['symbol']}·(z − {self._coord_to_str(ds['start'], l)}){seg_name}."
                    )

                for de in dist_ends:
                    sign = "−" if de['direction'] == 1 else "+"
                    parts.append(
                        f"На {seg_name.lower()} участке нужно ввести компенсацию от распределённой нагрузки {de['symbol']} с противоположным знаком, "
                        f"чтобы исключить действие данной нагрузки из уравнения продольных сил. "
                        f"Записываем: {sign} {de['symbol']}·(z − {self._coord_to_str(de['end'], l)}){seg_name}."
                    )

                for part in parts:
                    self._add_para(part, indent=1)

    def _build_expanded_equation(self, segment_equations, P, q, l, N0):
        """Строит раскрытое уравнение N(z) = N(0)_I - ..._II + ..._III"""
        seg_names = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
        parts = [f"N(z) = N(0){seg_names[1]}"]

        # Собираем все уникальные нагрузки
        all_loads = []
        seen = set()
        for seg_num in range(1, 5):
            for load in segment_equations.get(seg_num, []):
                key = (load['type'], load.get('symbol'), load.get('position', load.get('start', load.get('end'))))
                if key not in seen:
                    seen.add(key)
                    all_loads.append(load)

        for load in all_loads:
            seg = 1
            if load['type'] == 'force':
                # Определяем, на каком участке появляется сила
                for s in range(1, 5):
                    if any(ld['type'] == 'force' and ld['symbol'] == load['symbol']
                           for ld in segment_equations.get(s, [])):
                        seg = s
                        break
                sign = "−" if load['direction'] == 1 else "+"
                a_str = self._coord_to_str(load['position'], l)
                parts.append(f"{sign} {load['symbol']}·‹z − {a_str}›⁰{seg_names[seg]}")
            elif load['type'] == 'distributed_start':
                for s in range(1, 5):
                    if any(ld['type'] == 'distributed_start' and ld['symbol'] == load['symbol']
                           for ld in segment_equations.get(s, [])):
                        seg = s
                        break
                sign = "−" if load['direction'] == 1 else "+"
                a_str = self._coord_to_str(load['start'], l)
                parts.append(f"{sign} {load['symbol']}·(z − {a_str}){seg_names[seg]}")
            elif load['type'] == 'distributed_end':
                for s in range(1, 5):
                    if any(ld['type'] == 'distributed_end' and ld['symbol'] == load['symbol']
                           for ld in segment_equations.get(s, [])):
                        seg = s
                        break
                sign = "+" if load['direction'] == 1 else "−"
                a_str = self._coord_to_str(load['end'], l)
                parts.append(f"{sign} {load['symbol']}·(z − {a_str}){seg_names[seg]}")

        return " ".join(parts)

    def _write_detailed_segment_calculations(self, calc_results, segment_equations, P, q, l, N0):
        """Подробный расчёт по каждому участку с подстановками"""
        seg_names = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
        seg_keys = ['участок_1', 'участок_2', 'участок_3', 'участок_4']

        for seg_num, seg_key in zip(range(1, 5), seg_keys):
            if seg_key not in calc_results:
                continue

            data = calc_results[seg_key]
            z_start = data['z_start']
            z_end = data['z_end']
            N_start = data['N_start']
            N_end = data['N_end']
            seg_name = seg_names[seg_num]

            # Заголовок участка
            self._add_mixed([
                (f"{seg_name} участок  ", True, False),
                (f"{self._coord_to_str(z_start, l)} ≤ z ≤ {self._coord_to_str(z_end, l)}.", False, False)
            ])

            # Формула для участка
            loads = segment_equations.get(seg_num, [])
            formula_parts = [f"N(z) = N(0)"]

            seen = set()
            for load in loads:
                key = (load['type'], load.get('symbol'), load.get('position', load.get('start', load.get('end'))))
                if key in seen:
                    continue
                seen.add(key)

                if load['type'] == 'force':
                    sign = "−" if load['direction'] == 1 else "+"
                    a_str = self._coord_to_str(load['position'], l)
                    formula_parts.append(f"{sign} {load['symbol']}·‹z − {a_str}›")
                elif load['type'] == 'distributed_start':
                    sign = "−" if load['direction'] == 1 else "+"
                    a_str = self._coord_to_str(load['start'], l)
                    formula_parts.append(f"{sign} {load['symbol']}·(z − {a_str})")
                elif load['type'] == 'distributed_end':
                    sign = "+" if load['direction'] == 1 else "−"
                    a_str = self._coord_to_str(load['end'], l)
                    formula_parts.append(f"{sign} {load['symbol']}·(z − {a_str})")

            formula = " ".join(formula_parts)
            self._add_para(formula, indent=1)

            # Вычисление N(z_start)
            self._add_para(f"N({self._coord_to_str(z_start, l)}) = {N_start:.2f} кН.", indent=1)

            # Вычисление N(z_end) с подстановкой
            self._add_para(f"N({self._coord_to_str(z_end, l)}) = {N_end:.2f} кН.", indent=1)

    # =========================================================
    # ТАБЛИЦА ЗНАЧЕНИЙ
    # =========================================================
    def _write_table(self, calc_results):
        table = self.doc.add_table(rows=3, cols=9)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ["", "I участок", "I участок", "II участок", "II участок",
                   "III участок", "III участок", "IV участок", "IV участок"]
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(11)

        z_row = ["z"]
        N_row = ["N(z), кН"]

        for seg_key in ['участок_1', 'участок_2', 'участок_3', 'участок_4']:
            if seg_key in calc_results:
                data = calc_results[seg_key]
                z_row.append(f"{data['z_start']:.1f}")
                z_row.append(f"{data['z_end']:.1f}")
                N_row.append(f"{data['N_start']:.2f}")
                N_row.append(f"{data['N_end']:.2f}")

        for i, val in enumerate(z_row):
            cell = table.rows[1].cells[i]
            cell.text = val
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(11)

        for i, val in enumerate(N_row):
            cell = table.rows[2].cells[i]
            cell.text = val
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(11)

    # =========================================================
    # РАСЧЁТ НА ПРОЧНОСТЬ
    # =========================================================
    def _write_strength_calculation(self, input_data, N_max, section, final_section):
        sigma_allow = input_data['sigma_allow']
        sigma_allow_MPa = sigma_allow / 1e6

        self._add_para("Условие прочности по допускаемым напряжениям:", indent=1)
        self._add_para("σ_max ≤ [σ],  где  σ_max = |N|_max / F", indent=1.5)
        self._add_para("Определим минимальную площадь F_min сечения стержня, способную выдержать все нагрузки:", indent=1)

        F_min = abs(N_max) * 1e3 / sigma_allow

        self._add_para(
            f"F_min = |N|_max / [σ] = {abs(N_max)*1e3:.0f} / {sigma_allow:.0f} = {F_min:.4e} м²",
            indent=1.5
        )

        if section['shape'] == 'square':
            a_calc = section['a'] * 1000
            a_std = final_section['a'] * 1000
            self._add_para("Для квадратного сечения F = a², откуда:", indent=1)
            self._add_para(f"a = √F_min = √{F_min:.4e} = {a_calc:.3f} м = {a_calc:.2f} мм", indent=1.5)
            self._add_para(f"Из нормального ряда выбираем значение a = {a_std:.0f} мм.", indent=1)

        elif section['shape'] == 'rectangle_2_1':
            b_calc = section['b'] * 1000
            h_calc = section['h'] * 1000
            b_std = final_section['b'] * 1000
            h_std = final_section['h'] * 1000
            self._add_para("Из условия h = 2b, определим ширину b стержня. F = b·h = 2b², откуда:", indent=1)
            self._add_para(f"b = √(F_min/2) = √({F_min:.4e}/2) = {b_calc:.4f} м = {b_calc:.2f} мм", indent=1.5)
            self._add_para(f"h = 2b = {h_calc:.2f} мм", indent=1.5)
            self._add_para(f"Из нормального ряда выбираем значение b = {b_std:.0f} мм, h = {h_std:.0f} мм.", indent=1)

        elif section['shape'] == 'circle':
            d_calc = section['d'] * 1000
            d_std = final_section['d'] * 1000
            self._add_para("Для круглого сечения F = πd²/4, откуда:", indent=1)
            self._add_para(f"d = √(4F_min/π) = √(4·{F_min:.4e}/π) = {d_calc:.3f} м = {d_calc:.2f} мм", indent=1.5)
            self._add_para(f"Из нормального ряда выбираем значение d = {d_std:.0f} мм.", indent=1)

    # =========================================================
    # РАСЧЁТ НА ЖЁСТКОСТЬ
    # =========================================================
    def _write_stiffness_calculation(self, input_data, section):
        W_coeff = input_data['W_coeff']
        l = input_data['l']
        W_allow = W_coeff * l

        self._add_para(f"[W] = {W_coeff}·l = {W_coeff}·{l} = {W_allow:.4f} м", indent=1)

        if section['shape'] == 'square':
            a_std = section['a'] * 1000
            self._add_para(f"По условию жёсткости принимаем a = {a_std:.0f} мм.", indent=1)
        elif section['shape'] == 'rectangle_2_1':
            b_std = section['b'] * 1000
            h_std = section['h'] * 1000
            self._add_para(f"По условию жёсткости принимаем b = {b_std:.0f} мм, h = {h_std:.0f} мм.", indent=1)
        elif section['shape'] == 'circle':
            d_std = section['d'] * 1000
            self._add_para(f"По условию жёсткости принимаем d = {d_std:.0f} мм.", indent=1)

    # =========================================================
    # ОКОНЧАТЕЛЬНЫЙ ВЫБОР
    # =========================================================
    def _write_final_choice(self, final_section):
        if final_section['shape'] == 'square':
            a = final_section['a'] * 1000
            self._add_para(f"Сторона квадрата a = {a:.0f} мм.", indent=1)
        elif final_section['shape'] == 'rectangle_2_1':
            b = final_section['b'] * 1000
            h = final_section['h'] * 1000
            self._add_para(f"Ширина b = {b:.0f} мм, высота h = {h:.0f} мм.", indent=1)
        elif final_section['shape'] == 'circle':
            d = final_section['d'] * 1000
            self._add_para(f"Диаметр d = {d:.0f} мм.", indent=1)

    # =========================================================
    # ПРОВЕРКА ПРОЧНОСТИ
    # =========================================================
    def _write_strength_check(self, input_data, N_max, final_section):
        sigma_allow = input_data['sigma_allow']
        sigma_allow_MPa = sigma_allow / 1e6
        F_actual = final_section['F']
        sigma_actual = abs(N_max) * 1e3 / F_actual

        self._add_para("Определим нормальные напряжения для выбранного стержня в опасном сечении:", indent=1)

        if final_section['shape'] == 'square':
            a = final_section['a'] * 1000
            self._add_para(
                f"σ_max = |N|_max / F = |N|_max / a² = {abs(N_max)*1e3:.0f} / ({a:.0f}·10⁻³)² = {sigma_actual/1e6:.2f} МПа",
                indent=1.5
            )
        elif final_section['shape'] == 'rectangle_2_1':
            b = final_section['b'] * 1000
            h = final_section['h'] * 1000
            self._add_para(
                f"σ_max = |N|_max / (b·h) = {abs(N_max)*1e3:.0f} / ({b:.0f}·10⁻³ · {h:.0f}·10⁻³) = {sigma_actual/1e6:.2f} МПа",
                indent=1.5
            )
        elif final_section['shape'] == 'circle':
            d = final_section['d'] * 1000
            self._add_para(
                f"σ_max = |N|_max / (πd²/4) = {abs(N_max)*1e3:.0f} / (π·({d:.0f}·10⁻³)²/4) = {sigma_actual/1e6:.2f} МПа",
                indent=1.5
            )

        self._add_para(
            f"т.е. σ_max = {sigma_actual/1e6:.2f} МПа < [σ] = {sigma_allow_MPa:.0f} МПа, условие прочности выполняется.",
            indent=1
        )

    # =========================================================
    # ОТВЕТ
    # =========================================================
    def _write_answer(self, final_section):
        if final_section['shape'] == 'square':
            a = final_section['a'] * 1000
            self._add_para(f"Сторона квадрата a = {a:.0f} мм.", indent=0)
        elif final_section['shape'] == 'rectangle_2_1':
            b = final_section['b'] * 1000
            h = final_section['h'] * 1000
            self._add_para(f"Ширина b = {b:.0f} мм, высота h = {h:.0f} мм.", indent=0)
        elif final_section['shape'] == 'circle':
            d = final_section['d'] * 1000
            self._add_para(f"Диаметр d = {d:.0f} мм.", indent=0)

    # =========================================================
    # ИЗОБРАЖЕНИЕ
    # =========================================================
    def add_image(self, image_path, caption):
        if os.path.exists(image_path):
            self.doc.add_picture(image_path, width=Inches(5.5))
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(caption)
            run.font.size = Pt(10)
            run.italic = True
            run.font.name = 'Times New Roman'

    def save(self, filepath):
        self.doc.save(filepath)