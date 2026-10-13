from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QGroupBox, QFormLayout)
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
        return {
            "P": float(self.P_edit.text()) if self.P_edit.text() else 15,
            "q": float(self.q_edit.text()) if self.q_edit.text() else 15,
            "l": float(self.l_edit.text()) if self.l_edit.text() else 1,
            "sigma_allow": float(self.sigma_edit.text()) * 1e6 if self.sigma_edit.text() else 160e6,
            "E": float(self.E_edit.text()) * 1e6 if self.E_edit.text() else 200000e6,
            "W_coeff": float(self.W_coeff_edit.text()) if self.W_coeff_edit.text() else 0.002,
            "shape": self.shape_combo.currentIndex()
        }