from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFormLayout,
                             QDateEdit, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QDate

class TitleEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование титульника")
        self.resize(500, 400)
        
        self.teachers = [
            {"name": "Онищук С.Ю.", "position": "Ст. преп. каф. «Машиноведение»"},
            {"name": "Скирда А.А.", "position": "Доцент каф. «Машиноведение»"},
            {"name": "Другой...", "position": ""}
        ]
        
        self.create_ui()
    
    def create_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.student_edit = QLineEdit()
        self.student_edit.setPlaceholderText("Иванов И.И.")
        
        self.group_edit = QLineEdit()
        self.group_edit.setPlaceholderText("ОмГТУ-251")
        
        self.variant_edit = QLineEdit()
        self.variant_edit.setPlaceholderText("11-2-23-4")
        
        self.teacher_combo = QComboBox()
        for teacher in self.teachers:
            self.teacher_combo.addItem(teacher["name"])
        self.teacher_combo.currentTextChanged.connect(self.on_teacher_changed)
        
        self.custom_teacher_edit = QLineEdit()
        self.custom_teacher_edit.setVisible(False)
        self.custom_teacher_edit.setPlaceholderText("Введите ФИО преподавателя")
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        
        form.addRow("ФИО студента:", self.student_edit)
        form.addRow("Группа:", self.group_edit)
        form.addRow("Вариант:", self.variant_edit)
        form.addRow("Преподаватель:", self.teacher_combo)
        form.addRow("Свой преподаватель:", self.custom_teacher_edit)
        form.addRow("Дата:", self.date_edit)
        
        layout.addLayout(form)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def on_teacher_changed(self, text):
        if text == "Другой...":
            self.custom_teacher_edit.setVisible(True)
        else:
            self.custom_teacher_edit.setVisible(False)
    
    def get_data(self) -> dict:
        teacher_name = self.teacher_combo.currentText()
        if teacher_name == "Другой...":
            teacher_name = self.custom_teacher_edit.text()
        
        return {
            "student_name": self.student_edit.text(),
            "group": self.group_edit.text(),
            "variant": self.variant_edit.text(),
            "teacher": teacher_name,
            "date": self.date_edit.date().toString("dd.MM.yyyy")
        }