import sys
import os
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QMenuBar,
                             QMenu, QFileDialog, QMessageBox, QTabWidget, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt

from gui.input_panel import InputPanel
from gui.scheme_editor import SchemeEditor
from gui.title_editor import TitleEditor
from gui.plot_widget import PlotWidget
from gui.results_panel import ResultsPanel
from export.word_exporter import WordExporter
from core.report_data import ReportDataBuilder
from core.problem import make_calculator
from core.section import SectionSelector
from core.variants import get_variant_data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчёт стержня на растяжение-сжатие")
        self.resize(1400, 900)
        self.title_data = {
            "student_name": "",
            "group": "",
            "variant": "",
            "teacher": "Онищук С.Ю.",
            "teacher_position": "Ст. преп. каф.",
            "date": "",
            "teacher_date": ""
        }
        self.calculation_results = None
        self.dangerous_section = None
        self.section_strength = None
        self.section_stiffness = None
        self.final_section = None
        self.report_text = ""
        self.create_menu()
        self.create_central_widget()
        # Общий титульник из центрального окна объединённой программы.
        import json, re
        try: common=json.loads(os.environ.get('OMGTU_TITLE_JSON','{}'))
        except Exception: common={}
        for local,shared in [('student_name','student'),('group','group'),('variant','variant'),('teacher','teacher'),('date','date'),('teacher_date','teacher_date'),('teacher_position','position')]:
            if common.get(shared):self.title_data[local]=common[shared]
        match=re.fullmatch(r'\s*\d+\s*-\s*\d+\s*-\s*(\d+)\s*-\s*(\d+)\s*',common.get('variant',''))
        if match:
            row,scheme=map(int,match.groups())
            if 1<=row<=30 and 1<=scheme<=30:
                self.data_variant_combo.setCurrentIndex(row-1)
                self.scheme_editor.preset_combo.setCurrentIndex(scheme-1)
        if common.get('year'):self.title_data['year']=common['year']


    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        save_action = file_menu.addAction("Сохранить в Word...")
        save_action.triggered.connect(self.save_to_word)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
        title_menu = menubar.addMenu("Титульник")
        edit_title_action = title_menu.addAction("Редактировать титульник...")
        edit_title_action.triggered.connect(self.edit_title)
        help_menu = menubar.addMenu("Справка")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self.show_about)

    def create_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        calc_button = QPushButton("Рассчитать")
        calc_button.setObjectName("calcButton")
        calc_button.setStyleSheet(
            "QPushButton { font-size: 16px; padding: 12px 24px; "
            "background-color: #4CAF50; color: white; font-weight: bold; }")
        calc_button.clicked.connect(self.calculate)
        layout.addWidget(calc_button)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        input_tab = QWidget()
        input_layout = QVBoxLayout(input_tab)
        from PyQt6.QtWidgets import QGroupBox, QFormLayout
        variants = QGroupBox("Вариант исходных данных (приложение 1)")
        v_form = QFormLayout(variants)
        self.custom_data_check = QCheckBox("Свои исходные данные")
        self.data_variant_combo = QComboBox()
        for i in range(1, 31):
            self.data_variant_combo.addItem(f"Вариант № {i}", i)
        self.data_variant_combo.setCurrentIndex(10)
        v_form.addRow("Строка таблицы:", self.data_variant_combo)
        v_form.addRow(self.custom_data_check)
        input_layout.addWidget(variants)
        self.input_panel = InputPanel()
        self.input_panel.l_edit.textChanged.connect(self._on_l_changed)
        self.input_panel.P_edit.textChanged.connect(self._on_P_changed)
        self.input_panel.q_edit.textChanged.connect(self._on_q_changed)
        input_layout.addWidget(self.input_panel)
        self.data_variant_combo.currentIndexChanged.connect(self.apply_data_variant)
        self.custom_data_check.toggled.connect(self.apply_data_variant)
        self.tabs.addTab(input_tab, "Ввод данных")
        scheme_tab = QWidget()
        scheme_layout = QVBoxLayout(scheme_tab)
        self.scheme_editor = SchemeEditor()
        self.scheme_editor.model_changed.connect(self._invalidate_results)
        scheme_layout.addWidget(self.scheme_editor)
        self.apply_data_variant()  # Только после создания редактора схемы.
        self.tabs.addTab(scheme_tab, "Схема нагружения")
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        self.results_panel = ResultsPanel()
        results_layout.addWidget(self.results_panel)
        self.tabs.addTab(results_tab, "Результаты")
        plots_tab = QWidget()
        plots_layout = QVBoxLayout(plots_tab)
        self.plot_widget = PlotWidget()
        plots_layout.addWidget(self.plot_widget)
        self.tabs.addTab(plots_tab, "Эпюры")
        # Результаты становятся неактуальными сразу после изменения исходных данных.
        for field in (self.input_panel.P_edit, self.input_panel.q_edit,
                      self.input_panel.l_edit, self.input_panel.sigma_edit,
                      self.input_panel.E_edit, self.input_panel.W_coeff_edit):
            field.textChanged.connect(self._invalidate_results)
        self.input_panel.shape_combo.currentIndexChanged.connect(self._invalidate_results)
        self.input_panel.consider_stiffness_check.toggled.connect(self._invalidate_results)

    def _invalidate_results(self, *_):
        had_results = self.calculation_results is not None
        self.calculation_results = None
        self.report_text = ''
        self.final_section = None
        if had_results and hasattr(self, 'results_panel'):
            self.results_panel.mark_outdated()
        if had_results and hasattr(self, 'plot_widget'):
            self.plot_widget.figure.clear()
            self.plot_widget.canvas.draw()

    def apply_data_variant(self, *_):
        custom = self.custom_data_check.isChecked()
        self.data_variant_combo.setEnabled(not custom)
        for field in (self.input_panel.P_edit, self.input_panel.q_edit):
            field.setReadOnly(not custom)
        if not custom:
            P, q = get_variant_data(self.data_variant_combo.currentData())
            self.input_panel.P_edit.setText(str(P))
            self.input_panel.q_edit.setText(str(q))
        # По методическим указаниям l = 1 м для всех стандартных вариантов.
        self.input_panel.l_edit.setReadOnly(not custom)
        if not custom:
            self.input_panel.l_edit.setText('1')

    def _on_l_changed(self, text):
        try:
            l_value = float(text)
            self.scheme_editor.set_l_value(l_value)
        except ValueError:
            pass

    def _on_P_changed(self, text):
        try:
            P_value = float(text)
            self.scheme_editor.set_P_value(P_value)
        except ValueError:
            pass

    def _on_q_changed(self, text):
        try:
            q_value = float(text)
            self.scheme_editor.set_q_value(q_value)
        except ValueError:
            pass

    def edit_title(self):
        dialog = TitleEditor(self)
        title = dict(self.title_data)
        if not title.get('variant'):
            title['variant'] = self._suggested_variant()
        dialog.set_data(title)
        if dialog.exec():
            self.title_data = dialog.get_data()

    def _suggested_variant(self):
        # См. страницу 1 методички: первые ДВА числа для задачи №3,
        # последние ДВА — строка данных и схема задач №1,2,4–10.
        return (f"__-__-{self.data_variant_combo.currentData()}-"
                f"{self.scheme_editor.preset_number}")

    def calculate(self):
        try:
            input_data = self.input_panel.get_data()
            scheme = self.scheme_editor.get_scheme()
            l = input_data['l']
            P_value = input_data['P']
            q_value = input_data['q']
            boundary_conditions = self.scheme_editor.get_boundary_conditions()
            support_side = ('left' if self.scheme_editor.support_left_radio.isChecked()
                            else 'right')
            calc = make_calculator(
                scheme, P_value, q_value, l=l, support=support_side,
                boundary=boundary_conditions, E=input_data['E'])
            calc_results = calc.compute_at_boundaries()
            dangerous_section = calc.find_dangerous_section()
            shape_map = {0: 'square', 1: 'rectangle_2_1', 2: 'circle'}
            shape = shape_map[input_data['shape']]
            section_strength = SectionSelector.from_strength(
                dangerous_section[1], input_data['sigma_allow'], shape)
            section_stiffness = SectionSelector.from_stiffness(
                0, input_data['W_coeff'], l, input_data['E'],
                dangerous_section[1], shape, calculator=calc)
            # По образцу задачи №1 выбираем сечение ТОЛЬКО по прочности.
            # Жёсткость — дополнительная независимая проверка по выбору.
            final_section = (max((section_strength, section_stiffness),
                                 key=lambda section: section['F'])
                             if input_data['consider_stiffness'] else section_strength)
            self.calculation_results = calc_results
            self.dangerous_section = dangerous_section
            self.section_strength = section_strength
            self.section_stiffness = section_stiffness
            self.final_section = final_section
            self.results_panel.display_results(
                calc_results, dangerous_section,
                section_strength, section_stiffness, final_section,
                input_data['consider_stiffness'],
                calc.find_W_max(final_section['F'])[1],
                reaction=calc.support_reaction())
            z_values = []
            N_values = []
            for segment_name, data in calc_results.items():
                z_values.extend([data['z_start'], data['z_end']])
                N_values.extend([data['N_start'], data['N_end']])
            self.plot_widget.plot_N_diagram(
                z_values, N_values, dangerous_section[0],
                detailed=calc.compute_at_load_breakpoints())
            self.report_text = ReportDataBuilder.build_report(
                input_data, calc_results, dangerous_section,
                section_strength, section_stiffness, final_section)
            self.tabs.setCurrentIndex(2)
            QMessageBox.information(
                self, "Расчёт завершён", "Расчёт выполнен успешно!")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self, "Ошибка", f"Ошибка при расчёте:\n{str(e)}")

    def save_to_word(self):
        if not self.calculation_results:
            QMessageBox.warning(self, "Внимание", "Сначала выполните расчёт!")
            return
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения")
        if directory:
            surname = (self.title_data['student_name'].strip().split()[0]
                       if self.title_data['student_name'] else "Студент")
            variant = (self.title_data['variant']
                       if self.title_data['variant'] else "вариант")
            filename = f"{surname}_{variant}.docx"
            filepath = os.path.join(directory, filename)
            try:
                from teacher_exact import create_tension_docx
                data=self.input_panel.get_data()
                title=dict(self.title_data)
                if not title['variant']:title['variant']=self._suggested_variant()
                mapped={'student':title.get('student_name',''),'group':title.get('group',''),
                        'variant':title.get('variant',''),'teacher':title.get('teacher',''),
                        'position':title.get('teacher_position',''),'date':title.get('date',''),
                        'teacher_date':title.get('teacher_date',''),'year':title.get('year','2026')}
                create_tension_docx(filepath,self.scheme_editor.get_scheme(),data,mapped,
                    fixed=('left' if self.scheme_editor.support_left_radio.isChecked() else 'right'),
                    boundary=self.scheme_editor.get_boundary_conditions(),
                    teacher_scheme=(self.scheme_editor.preset_number if not self.scheme_editor.custom_scheme else 0))
                QMessageBox.information(
                    self, "Сохранение", f"Файл сохранён:\n{filepath}")
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(
                    self, "Ошибка", f"Ошибка при сохранении:\n{str(e)}")

    def _build_scheme_description(self, scheme, input_data):
        P = input_data['P']
        q = input_data['q']
        parts = []
        for seg_idx, seg_loads in enumerate(scheme):
            for load in seg_loads:
                count = load['count']
                direction = "вправо" if load['direction'] == 1 else "влево"
                if load['type'] == 'force':
                    parts.append(
                        f"на участке {seg_idx+1} сила {count}P={count*P} кН {direction}")
                elif load['type'] == 'distributed':
                    parts.append(
                        f"на участке {seg_idx+1} нагрузка {count}q={count*q} кН/м {direction}")
        support = ("слева" if self.scheme_editor.support_left_radio.isChecked()
                   else "справа")
        return f"Опора {support}; " + "; ".join(parts) + "."

    def show_about(self):
        QMessageBox.about(
            self, "О программе",
            "Расчёт стержня на растяжение-сжатие\n"
            "Версия 7.0\n\n"
            "Программа для решения задач сопромата")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())