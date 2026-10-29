from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QGroupBox, QFormLayout, QCheckBox)
from PyQt6.QtCore import Qt

class InputPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.create_ui()
    
    def create_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        header = QLabel("Исходные данные")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Параметры нагрузки
        load_group = QGroupBox("Параметры нагрузки")
        load_layout = QFormLayout()
        load_layout.setSpacing(10)
        
        self.P_edit = QLineEdit("15")
        self.P_edit.setPlaceholderText("кН")
        self.P_edit.textChanged.connect(self._on_value_changed)
        
        self.q_edit = QLineEdit("15")
        self.q_edit.setPlaceholderText("кН/м")
        self.q_edit.textChanged.connect(self._on_value_changed)
        
        self.l_edit = QLineEdit("1")
        self.l_edit.setPlaceholderText("м")
        self.l_edit.textChanged.connect(self._on_value_changed)
        
        load_layout.addRow("P, кН:", self.P_edit)
        load_layout.addRow("q, кН/м:", self.q_edit)
        load_layout.addRow("l, м:", self.l_edit)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Материал и допуски
        material_group = QGroupBox("Материал и допуски")
        material_layout = QFormLayout()
        material_layout.setSpacing(10)
        
        self.sigma_edit = QLineEdit("160")
        self.sigma_edit.setPlaceholderText("МПа")
        
        self.E_edit = QLineEdit("200000")
        self.E_edit.setPlaceholderText("МПа")
        
        self.W_coeff_edit = QLineEdit("0.002")
        
        material_layout.addRow("[σ], МПа:", self.sigma_edit)
        material_layout.addRow("E, МПа:", self.E_edit)
        material_layout.addRow("Коэф. [W]:", self.W_coeff_edit)
        
        self.consider_stiffness_check = QCheckBox(
            'Дополнительно учитывать жёсткость при подборе (не требуется в задаче №1)')
        self.consider_stiffness_check.setChecked(False)
        material_layout.addRow(self.consider_stiffness_check)

        material_group.setLayout(material_layout)
        layout.addWidget(material_group)
        
        # Форма сечения
        section_group = QGroupBox("Форма сечения")
        section_layout = QFormLayout()
        section_layout.setSpacing(10)
        
        self.shape_combo = QComboBox()
        self.shape_combo.addItems([
            "Квадрат (a × a)", 
            "Прямоугольник (h = 2b)", 
            "Круг (d)"
        ])
        
        self.shape_combo.setCurrentIndex(1)  # В задаче № 1 преподаватель требует h = 2b.
        section_layout.addRow("Форма:", self.shape_combo)
        
        section_group.setLayout(section_layout)
        layout.addWidget(section_group)
        
        layout.addStretch()
    
    def _on_value_changed(self):
        """Уведомить родительское окно об изменении значений"""
        try:
            P = float(self.P_edit.text())
            q = float(self.q_edit.text())
            l = float(self.l_edit.text())
            
            # Передаём в scheme_editor через родительское окно
            parent = self.parent()
            while parent and not hasattr(parent, 'scheme_editor'):
                parent = parent.parent()
            
            if parent and hasattr(parent, 'scheme_editor'):
                parent.scheme_editor.set_P_value(P)
                parent.scheme_editor.set_q_value(q)
                parent.scheme_editor.set_l_value(l)
        except ValueError:
            pass
    
    def get_data(self) -> dict:
        """Строгий ввод: пустые/неверные значения не заменяются умолчаниями."""
        import math

        def number(field, name):
            raw = field.text().strip().replace(',', '.')
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError(f'{name}: укажите число') from exc
            if not math.isfinite(value):
                raise ValueError(f'{name}: число должно быть конечным')
            return value

        P = number(self.P_edit, 'P')
        q = number(self.q_edit, 'q')
        l = number(self.l_edit, 'l')
        E = number(self.E_edit, 'E')
        sigma = number(self.sigma_edit, '[σ]')
        W_coeff = number(self.W_coeff_edit, '[W]')
        if P < 0 or q < 0:
            raise ValueError('P и q должны быть неотрицательными; направление задаётся стрелкой')
        if l <= 0 or E <= 0 or sigma <= 0 or W_coeff <= 0:
            raise ValueError('l, E, [σ] и коэффициент [W] должны быть положительными')
        return {'P': P, 'q': q, 'l': l, 'sigma_allow': sigma*1e6,
                'E': E*1e6, 'W_coeff': W_coeff,
                'shape': self.shape_combo.currentIndex(),
                'consider_stiffness': self.consider_stiffness_check.isChecked()}
