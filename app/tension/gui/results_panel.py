from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.create_ui()
    
    def create_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("<b>Результаты расчета</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Таблица значений N(z)
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Участок I", "Участок I", "Участок II", "Участок II",
            "Участок III", "Участок III", "Участок IV", "Участок IV"
        ])
        self.table.setRowCount(2)
        self.table.setVerticalHeaderLabels(["z, м", "N(z), кН"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # Текстовый вывод
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)
    
    def mark_outdated(self):
        """Не показывать старые результаты после изменения расчётной модели."""
        self.table.clearContents()
        self.text_output.setPlainText(
            'Исходные данные или схема изменены. Нажмите «Рассчитать», '
            'чтобы получить актуальные значения N(z), сечение и эпюру.')

    def display_results(self, calc_results, dangerous_section, section_strength,
                        section_stiffness, final_section=None, consider_stiffness=False,
                        w_final=None, reaction=None):
        """Отобразить результаты расчета"""
        # Заполняем таблицу
        col = 0
        for segment_name, data in calc_results.items():
            self.table.setItem(0, col, QTableWidgetItem(f"{data['z_start']:.1f}"))
            self.table.setItem(1, col, QTableWidgetItem(f"{data['N_start']:.2f}"))
            col += 1
            
            self.table.setItem(0, col, QTableWidgetItem(f"{data['z_end']:.1f}"))
            self.table.setItem(1, col, QTableWidgetItem(f"{data['N_end']:.2f}"))
            col += 1
        
        # Текстовый вывод
        text = f"=== ОПАСНОЕ СЕЧЕНИЕ ===\n"
        text += f"z = {dangerous_section[0]:.1f} м\n"
        text += f"|N|max = {dangerous_section[1]:.2f} кН\n"
        if reaction is not None:
            text += f"Реакция закреплённого конца Rz = {reaction:.3f} кН\n"
        text += "\n"
        
        text += f"=== ПОДБОР СЕЧЕНИЯ ПО ПРОЧНОСТИ ===\n"
        if section_strength['shape'] == 'square':
            text += f"Форма: квадрат\n"
            text += f"a = {section_strength['a']*1000:.2f} мм\n"
            text += f"F = {section_strength['F']*1e6:.2f} мм²\n"
        elif section_strength['shape'] == 'rectangle_2_1':
            text += f"Форма: прямоугольник (h=2b)\n"
            text += f"b = {section_strength['b']*1000:.2f} мм\n"
            text += f"h = {section_strength['h']*1000:.2f} мм\n"
            text += f"F = {section_strength['F']*1e6:.2f} мм²\n"
        elif section_strength['shape'] == 'circle':
            text += f"Форма: круг\n"
            text += f"d = {section_strength['d']*1000:.2f} мм\n"
            text += f"F = {section_strength['F']*1e6:.2f} мм²\n"
        
        text += f"\n=== ПОДБОР СЕЧЕНИЯ ПО ЖЕСТКОСТИ ===\n"
        if section_stiffness['shape'] == 'square':
            text += f"Форма: квадрат\n"
            text += f"a = {section_stiffness['a']*1000:.2f} мм\n"
            text += f"F = {section_stiffness['F']*1e6:.2f} мм²\n"
        elif section_stiffness['shape'] == 'rectangle_2_1':
            text += f"Форма: прямоугольник (h=2b)\n"
            text += f"b = {section_stiffness['b']*1000:.2f} мм\n"
            text += f"h = {section_stiffness['h']*1000:.2f} мм\n"
            text += f"F = {section_stiffness['F']*1e6:.2f} мм²\n"
        elif section_stiffness['shape'] == 'circle':
            text += f"Форма: круг\n"
            text += f"d = {section_stiffness['d']*1000:.2f} мм\n"
            text += f"F = {section_stiffness['F']*1e6:.2f} мм²\n"
        
        if final_section is not None:
            text += "\n=== ПРИНЯТОЕ СЕЧЕНИЕ ===\n"
            text += ("По прочности и жёсткости\n" if consider_stiffness
                     else "Только по прочности (по условию задачи №1)\n")
            if final_section['shape'] == 'rectangle_2_1':
                text += (f"b = {final_section['b']*1000:g} мм, "
                         f"h = {final_section['h']*1000:g} мм\n")
            elif final_section['shape'] == 'circle':
                text += f"d = {final_section['d']*1000:g} мм\n"
            else:
                text += f"a = {final_section['a']*1000:g} мм\n"
            if w_final is not None:
                text += (f"Максимальное осевое перемещение |W|max = {w_final*1000:.3f} мм\n"
                         "(определено интегрированием N/(E·F); для задачи №1 — справочно).\n")
        self.text_output.setPlainText(text)