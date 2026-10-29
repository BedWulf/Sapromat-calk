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
            section.left_margin = Cm(2)
            section.right_margin = Cm(2)

    def _add_para(self, text, bold=False, italic=False, size=12, align=None, indent=None):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
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
        """Титул построен на ОРИГИНАЛЬНОЙ странице 2 преподавателя.

        Сохраняем её Word-разметку, промежутки, отступы, выравнивание и
        шрифт 14 пт, заменяя только персональные данные. Никаких выдуманных
        фамилий/групп или номеров других задач.
        """
        template_path = os.path.join(os.path.dirname(__file__), 'assets',
                                     'teacher_title_template.docx')
        if not os.path.exists(template_path):
            raise FileNotFoundError('Отсутствует шаблон титульника: ' + template_path)
        self.doc = Document(template_path)
        paras = self.doc.paragraphs
        assert len(paras) == 29, 'Изменена структура шаблона титульного листа'

        def set_text(index, content):
            p = paras[index]
            # Сохраняем параметры абзаца; для изменяемого текста создаём
            # один Times New Roman run, чтобы не распадались фамилии на куски.
            p.clear()
            r = p.add_run(content)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(14)
            return p

        display_variant = title_data.get('variant', '').strip() or '___-___-___-___'
        set_text(36 - 21, 'Вариант: ' + display_variant)
        group = title_data.get('group', '').strip() or '________'
        student = title_data.get('student_name', '').strip() or '________________'
        set_text(40 - 21, 'Выполнил: ст. гр.' + group)
        set_text(41 - 21, student + ' __________')
        date = title_data.get('date', '').strip()
        set_text(42 - 21, 'Дата:          ' + (date or '__________'))
        position = title_data.get('teacher_position', 'Ст. преп. каф.').strip() or 'Ст. преп. каф.'
        set_text(43 - 21, 'Проверил: ' + position)
        teacher = title_data.get('teacher', '').strip() or '________________'
        set_text(45 - 21, teacher + ' _____________')
        date_checked = title_data.get('teacher_date', '').strip()
        set_text(46 - 21, 'Дата:          ' + (date_checked or '__________'))
        # Исходная дата титула из образца — Омск, 2026 год. Можно задать год.
        year = str(title_data.get('year', '2026')).strip() or '2026'
        set_text(49 - 21, 'Омск – ' + year)
        # Не вставляем пустой абзац с page break: титульник заполняет
        # почти весь лист и такой абзац мог создать пустую страницу.

    # =========================================================
    # ПОЛНЫЙ ТЕКСТ РАСЧЁТА
    # =========================================================
    def add_calculation_text(self, input_data, calc_results,
                             dangerous_section, section_strength,
                             section_stiffness, final_section,
                             scheme=None, boundary_conditions=None, support_left=False):
        P = input_data['P']
        q = input_data['q']
        l = input_data['l']
        sigma = input_data['sigma_allow'] / 1e6
        E = input_data['E'] / 1e6
        W_coeff = input_data['W_coeff']

        shape_names = {0: 'квадрат', 1: 'прямоугольник (h = 2b)', 2: 'круг'}
        shape = shape_names.get(input_data['shape'], 'квадрат')

        # ===== ЗАГОЛОВОК =====
        first_heading = self._add_para("ЗАДАЧА 1. Растяжение – сжатие.", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
        first_heading.paragraph_format.page_break_before = True

        # ===== ДАНО (стр. 3 преподавателя) =====
        self._add_para('Дано: значение нагрузок (см. прил. 1), схема нагружения, '
                       'способ закрепления и координаты приложения нагрузок (прил. 2).')
        from tempfile import TemporaryDirectory
        from export.scheme_plot import save_scheme_plot
        with TemporaryDirectory() as tmp:
            only_scheme = os.path.join(tmp, 'scheme.png')
            save_scheme_plot(scheme or [], input_data, support_left, only_scheme)
            data_table = self.doc.add_table(rows=2, cols=5)
            data_table.style = 'Table Grid'
            data_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            data_table.autofit = False
            headers = ('Схема нагружения', 'P, кН', 'q, кН/м', 'l, м', '[σ], МПа')
            vals = (None, f'{P:g}', f'{q:g}', f'{l:g}', f'{sigma:g}')
            for j, header in enumerate(headers):
                c = data_table.cell(0,j)
                c.text = header
                for r in c.paragraphs[0].runs: r.font.size = Pt(9)
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                c.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
                c.paragraphs[0].paragraph_format.left_indent = Cm(0)
            for j,val in enumerate(vals):
                c = data_table.cell(1,j)
                if val is not None: c.text = val
                else:
                    c.paragraphs[0].add_run().add_picture(only_scheme, width=Cm(6.3))
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                c.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
                c.paragraphs[0].paragraph_format.left_indent = Cm(0)
                for r in c.paragraphs[0].runs: r.font.size = Pt(10)
            # Для изображения — широкий первый столбец.
            widths = [Cm(7.2), Cm(2.3), Cm(2.4), Cm(1.8), Cm(3.2)]
            for j,w in enumerate(widths):
                data_table.columns[j].width = w
            for row in data_table.rows:
                for j,w in enumerate(widths): row.cells[j].width = w
        self._add_para('Поперечное сечение: ' + shape + '.', size=11)

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

        # На стр. 3 преподаватель повторяет схему с делением на участки.
        if scheme:
            from tempfile import TemporaryDirectory
            from export.scheme_plot import save_scheme_plot
            with TemporaryDirectory() as temporary:
                scheme_only_path = os.path.join(temporary, 'load_scheme.png')
                save_scheme_plot(scheme, input_data, support_left, scheme_only_path)
                p_img = self.doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.add_run().add_picture(scheme_only_path, width=Cm(12.5))

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

        # На свободном конце известно ОДНО Г.У., второе вычисляется из
        # суммы внутренних нагрузок. При левой заделке N(4l) известно,
        # при правой — N(0). Точно так же делает интерфейс программы.
        from core.problem import make_calculator
        verified = make_calculator(scheme or [[], [], [], []], P, q, l=l,
                                   support='left' if support_left else 'right',
                                   boundary=boundary_conditions)
        bvals = verified.boundary_values()
        N0, N4l = bvals['N_left'], bvals['N_right']
        total = verified._total_internal_load()
        if support_left:
            self._add_para(f'Г.У. (свободный правый конец): N(4l) = {N4l:.3f} кН.', indent=1)
            self._add_para(f'Из равновесия: N(0) = N(4l) + ΣFz = '
                           f'{N4l:.3f} + ({total:.3f}) = {N0:.3f} кН.', indent=1)
        else:
            self._add_para(f'Г.У. (свободный левый конец): N(0) = {N0:.3f} кН.', indent=1)
            self._add_para(f'Из равновесия: N(4l) = N(0) − ΣFz = '
                           f'{N0:.3f} − ({total:.3f}) = {N4l:.3f} кН.', indent=1)

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

        # Схема и эпюра размещаются непосредственно после таблицы (образец, стр. 5).
        if scheme:
            from tempfile import TemporaryDirectory
            from export.scheme_plot import save_scheme_plot
            with TemporaryDirectory() as temporary:
                diagram_path = os.path.join(temporary, 'scheme_and_N.png')
                save_scheme_plot(scheme, input_data, support_left, diagram_path,
                                 verified.compute_at_load_breakpoints())
                self.doc.add_picture(diagram_path, width=Cm(16.2))

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
        if input_data.get('consider_stiffness', False):
            self._add_para('Дополнительная проверка по жёсткости [W] = '
                           f"{input_data['W_coeff']}·l: сечение выбрано по "
                           'более строгому из двух условий.', indent=1)

        # п.10 — проверка прочности
        self._add_mixed([("10. ", True, False),
                         ("Проверка прочности выбранного сечения.", False, False)])
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
                        if load['position'] <= 1e-9 or load['position'] >= 4*l-1e-9:
                            continue
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
                terms.append(f"{sign_start} {load['symbol']}·‹z − {a_str}›¹")
                terms.append(f"{sign_end} {load['symbol']}·‹z − {b_str}›¹")

        # Собираем уравнение
        if terms:
            inner = " ".join(terms)
            equation = f"N(z) = N(0) − [ {inner} ]"
        else:
            equation = "N(z) = N(0)"

        # Вклад каждой силы включается только ПОСЛЕ точки приложения,
        # а компенсация распределённой нагрузки — только ПОСЛЕ её конца.
        # Иначе, например, на участке II ошибочно появлялось 2q(z-2l),
        # хотя он начинается только на участке III.
        segment_equations = {1: [], 2: [], 3: [], 4: []}

        def first_segment(coordinate):
            return max(1, min(5, int(round(coordinate / l)) + 1))

        for load in loads_info:
            if load['type'] == 'force':
                begin = first_segment(load['position'])
                for seg in range(begin,5):
                    segment_equations[seg].append({
                        'type':'force', 'symbol':load['symbol'],
                        'direction':load['direction'], 'position':load['position'],
                        'value':load['value'], 'first_segment':begin})
            else:
                first = first_segment(load['start'])
                compensation = first_segment(load['end'])
                for seg in range(first,5):
                    segment_equations[seg].append({
                        'type':'distributed_start','symbol':load['symbol'],
                        'direction':load['direction'],'start':load['start'],
                        'value':load['value'], 'first_segment':first})
                for seg in range(compensation,5):
                    segment_equations[seg].append({
                        'type':'distributed_end','symbol':load['symbol'],
                        'direction':load['direction'],'end':load['end'],
                        'value':load['value'], 'first_segment':compensation})

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
            loads = [ld for ld in segment_equations.get(seg_num, [])
                     if ld['first_segment'] == seg_num]
            seg_name = seg_names[seg_num]

            if not loads:
                self._add_para(
                    f"{seg_name}. На участке {seg_name} мысленно закрываем всё, что расположено справа от черты S, "
                    f"новых сил на рассматриваемом участке нет.",
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
                        f"На участке {seg_name} действует сосредоточенная сила {fs['symbol']}={fs['value']} кН, {direction_str}. "
                        f"Поэтому записываем: {sign} {fs['symbol']}{seg_name}."
                    )

                for ds in dist_starts:
                    direction_str = "сонаправлена оси 0z" if ds['direction'] == 1 else "направлена против оси 0z"
                    sign = "+" if ds['direction'] == 1 else "−"
                    parts.append(
                        f"На участке {seg_name} действует распределённая нагрузка {ds['symbol']}={ds['value']} кН/м, {direction_str}. "
                        f"Продольная сила от этой нагрузки равняется произведению её величины на длину участка. "
                        f"Поэтому записываем: {sign} {ds['symbol']}·(z − {self._coord_to_str(ds['start'], l)}){seg_name}."
                    )

                for de in dist_ends:
                    sign = "−" if de['direction'] == 1 else "+"
                    parts.append(
                        f"На участке {seg_name} нужно ввести компенсацию от распределённой нагрузки {de['symbol']} с противоположным знаком, "
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
            seg = load['first_segment']
            if load['type'] == 'force':
                sign = '−' if load['direction'] == 1 else '+'
                a_str = self._coord_to_str(load['position'], l)
                parts.append(f"{sign} {load['symbol']}·‹z − {a_str}›⁰{seg_names[seg]}")
            elif load['type'] == 'distributed_start':
                sign = '−' if load['direction'] == 1 else '+'
                a_str = self._coord_to_str(load['start'], l)
                parts.append(f"{sign} {load['symbol']}·(z − {a_str}){seg_names[seg]}")
            elif load['type'] == 'distributed_end':
                sign = '+' if load['direction'] == 1 else '−'
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
        """Таблица: I–IV как 4 объединённых заголовка, 8 граничных точек."""
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        table = self.doc.add_table(rows=3, cols=9)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        widths = [Cm(1.8)] + [Cm(1.875)]*8
        for i,w in enumerate(widths): table.columns[i].width = w
        for row in table.rows:
            for i,w in enumerate(widths): row.cells[i].width = w
        table.cell(0,0).text = ''
        for seg in range(4):
            start_col = 1 + 2*seg
            merged = table.cell(0,start_col).merge(table.cell(0,start_col+1))
            merged.text = ('I', 'II', 'III', 'IV')[seg] + ' участок'
        table.cell(1,0).text = 'z'
        table.cell(2,0).text = 'N(z), кН'
        coords = []
        numbers = []
        for k in range(1,5):
            seg = calc_results[f'участок_{k}']
            coords += ['0' if k==1 else ('l' if k==2 else f'{k-1}l'),
                       'l' if k==1 else f'{k}l']
            numbers += [f"{seg['N_start']:.3f}".rstrip('0').rstrip('.'),
                        f"{seg['N_end']:.3f}".rstrip('0').rstrip('.')]
        for i, val in enumerate(coords, 1): table.cell(1,i).text = val
        for i, val in enumerate(numbers, 1): table.cell(2,i).text = val
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    paragraph.paragraph_format.space_after = Pt(0)
                    paragraph.paragraph_format.first_line_indent = Cm(0)
                    paragraph.paragraph_format.left_indent = Cm(0)
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
                        run.font.name = 'Times New Roman'
        return table

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
            a_calc = (F_min ** 0.5) * 1000  # До округления!
            a_std = final_section['a'] * 1000
            self._add_para("Для квадратного сечения F = a², откуда:", indent=1)
            self._add_para(f"a_min = √F_min = √{F_min:.4e} м² = {a_calc:.3f} мм", indent=1.5)
            self._add_para(f"Из нормального ряда выбираем значение a = {a_std:.0f} мм.", indent=1)

        elif section['shape'] == 'rectangle_2_1':
            b_calc = (F_min / 2) ** 0.5 * 1000  # До округления!
            h_calc = 2 * b_calc
            b_std = final_section['b'] * 1000
            h_std = final_section['h'] * 1000
            self._add_para("Из условия h = 2b, определим ширину b стержня. F = b·h = 2b², откуда:", indent=1)
            self._add_para(f"b_min = √(F_min/2) = √({F_min:.4e}/2) м = {b_calc:.3f} мм", indent=1.5)
            self._add_para(f"h = 2b = {h_calc:.2f} мм", indent=1.5)
            self._add_para(f"Из нормального ряда выбираем значение b = {b_std:.0f} мм, h = {h_std:.0f} мм.", indent=1)

        elif section['shape'] == 'circle':
            d_calc = (4 * F_min / math.pi) ** 0.5 * 1000  # До округления!
            d_std = final_section['d'] * 1000
            self._add_para("Для круглого сечения F = πd²/4, откуда:", indent=1)
            self._add_para(f"d_min = √(4F_min/π) = √(4·{F_min:.4e}/π) м = {d_calc:.3f} мм", indent=1.5)
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
            f"т.е. σ_max = {sigma_actual/1e6:.2f} МПа ≤ [σ] = {sigma_allow_MPa:.0f} МПа, условие прочности выполняется.",
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