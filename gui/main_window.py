import sys
import os
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QMenuBar,
                             QMenu, QFileDialog, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt

from gui.input_panel import InputPanel
from gui.scheme_editor import SchemeEditor
from gui.title_editor import TitleEditor
from gui.plot_widget import PlotWidget
from gui.results_panel import ResultsPanel
from export.word_exporter import WordExporter
from core.report_data import ReportDataBuilder
from core.rod import Rod
from core.loads import ConcentratedForce, DistributedLoad, Direction
from core.calculator import Calculator
from core.section import SectionSelector


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
            "date": ""
        }
        self.calculation_results = None
        self.dangerous_section = None
        self.section_strength = None
        self.section_stiffness = None
        self.final_section = None
        self.report_text = ""
        self.create_menu()
        self.create_central_widget()

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
        self.input_panel = InputPanel()
        self.input_panel.l_edit.textChanged.connect(self._on_l_changed)
        self.input_panel.P_edit.textChanged.connect(self._on_P_changed)
        self.input_panel.q_edit.textChanged.connect(self._on_q_changed)
        # Связь "выбор варианта -> автонастройка схемы нагружения"
        self.input_panel.variant_selected.connect(self._on_variant_selected)
        input_layout.addWidget(self.input_panel)
        self.tabs.addTab(input_tab, "Ввод данных")
        scheme_tab = QWidget()
        scheme_layout = QVBoxLayout(scheme_tab)
        self.scheme_editor = SchemeEditor()
        scheme_layout.addWidget(self.scheme_editor)
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

    def _on_variant_selected(self, variant) -> None:
        """Слот: пользователь выбрал вариант в InputPanel.

        Автоматически конфигурирует редактор схемы нагружения
        (нагрузки, направления, кратности, закрепление).

        Args:
            variant: core.variants_db.VariantData или None (ручной ввод).
        """
        # SchemeEditor создаётся позже InputPanel в create_central_widget,
        # поэтому защищаемся от сигнала при инициализации.
        editor = getattr(self, "scheme_editor", None)
        if editor is not None:
            editor.load_variant_scheme(variant)
        if variant is not None and not self.title_data.get("variant"):
            # Подставить номер варианта в титульник, если он ещё пуст
            self.title_data["variant"] = f"Вариант {variant.variant_id}"

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
        if dialog.exec():
            self.title_data = dialog.get_data()

    def calculate(self):
        try:
            input_data = self.input_panel.get_data()
            scheme = self.scheme_editor.get_scheme()
            l = input_data['l']
            total_length = 4 * l
            rod = Rod(total_length=total_length, n_segments=4)
            boundary_conditions = self.scheme_editor.get_boundary_conditions()
            if boundary_conditions["N_left"] is not None:
                rod.set_boundary(left=boundary_conditions["N_left"])
            elif boundary_conditions["N_right"] is not None:
                rod.set_boundary(right=boundary_conditions["N_right"])
            else:
                raise ValueError("Не задано граничное условие N(0) или N(4l)")
            P_value = input_data['P']
            q_value = input_data['q']
            for segment_loads in scheme:
                for load in segment_loads:
                    direction = Direction.POSITIVE if load['direction'] == 1 else Direction.NEGATIVE
                    if load['type'] == 'force':
                        is_at_free_end = False
                        if boundary_conditions["N_left"] is not None:
                            if abs(load['position']) < 0.01:
                                is_at_free_end = True
                        elif boundary_conditions["N_right"] is not None:
                            if abs(load['position'] - total_length) < 0.01:
                                is_at_free_end = True
                        if not is_at_free_end:
                            actual_value = load['count'] * P_value
                            rod.add_load(ConcentratedForce(
                                start=load['position'],
                                magnitude=actual_value,
                                direction=direction))
                    elif load['type'] == 'distributed':
                        actual_value = load['count'] * q_value
                        rod.add_load(DistributedLoad(
                            start=load['start'],
                            end=load['end'],
                            intensity=actual_value,
                            direction=direction))
            calc = Calculator(rod)
            calc_results = calc.compute_at_boundaries()
            dangerous_section = calc.find_dangerous_section()
            shape_map = {0: 'square', 1: 'rectangle_2_1', 2: 'circle'}
            shape = shape_map[input_data['shape']]
            section_strength = SectionSelector.from_strength(
                dangerous_section[1], input_data['sigma_allow'], shape)
            section_stiffness = SectionSelector.from_stiffness(
                0.001, input_data['W_coeff'], l, input_data['E'],
                dangerous_section[1], shape)
            if section_strength['F'] > section_stiffness['F']:
                final_section = section_strength
            else:
                final_section = section_stiffness
            self.calculation_results = calc_results
            self.dangerous_section = dangerous_section
            self.section_strength = section_strength
            self.section_stiffness = section_stiffness
            self.final_section = final_section
            self.results_panel.display_results(
                calc_results, dangerous_section,
                section_strength, section_stiffness)
            z_values = []
            N_values = []
            for segment_name, data in calc_results.items():
                z_values.extend([data['z_start'], data['z_end']])
                N_values.extend([data['N_start'], data['N_end']])
            self.plot_widget.plot_N_diagram(
                z_values, N_values, dangerous_section[0])
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
                exporter = WordExporter()
                exporter.create_title_page(self.title_data)
                input_data = self.input_panel.get_data()
                scheme = self.scheme_editor.get_scheme()
                boundary_conditions = self.scheme_editor.get_boundary_conditions()
                exporter.add_calculation_text(
                    input_data, self.calculation_results,
                    self.dangerous_section, self.section_strength,
                    self.section_stiffness, self.final_section,
                    scheme=scheme,
                    boundary_conditions=boundary_conditions)
                plot_path = os.path.join(directory, "plot_N.png")
                self.plot_widget.figure.savefig(
                    plot_path, dpi=150, bbox_inches='tight')
                exporter.add_image(
                    plot_path, "Рис. 1 — Эпюра продольной силы N(z)")
                exporter.save(filepath)
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
            "Версия 1.0\n\n"
            "Программа для решения задач сопромата")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())