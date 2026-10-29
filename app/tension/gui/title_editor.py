"""Поля титульного листа в оформлении преподавателя (ОмГТУ)."""
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QLineEdit, QComboBox,
                             QDialog, QDialogButtonBox, QFormLayout)


class TitleEditor(QDialog):
    TEACHERS = [
        ('Онищук С.Ю.', 'Ст. преп. каф.'),
        ('Скирда А.А.', 'Доцент каф.'),
        ('Другой...', ''),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Титульный лист по образцу ОмГТУ')
        self.resize(520, 420)
        form = QFormLayout()
        self.student_edit = QLineEdit()
        self.student_edit.setPlaceholderText('Иванов И.И.')
        self.group_edit = QLineEdit()
        self.group_edit.setPlaceholderText('ОмГТУ-251')
        self.variant_edit = QLineEdit()
        self.variant_edit.setPlaceholderText('11-2-23-4')
        self.variant_note = QLabel('Формат преподавателя — 4 числа. Последние два — строка данных и схема задачи №1. Первые два относятся к задаче №3 и заполняются отдельно.')
        self.variant_note.setWordWrap(True)
        self.teacher_combo = QComboBox()
        for name, _ in self.TEACHERS:
            self.teacher_combo.addItem(name)
        self.custom_teacher_edit = QLineEdit()
        self.custom_teacher_edit.setPlaceholderText('ФИО преподавателя')
        self.teacher_position_edit = QLineEdit('Ст. преп. каф.')
        self.student_date_edit = QLineEdit()
        self.student_date_edit.setPlaceholderText('дд.мм.гггг или оставить пустым')
        self.teacher_date_edit = QLineEdit()
        self.teacher_date_edit.setPlaceholderText('Дата проверки (необязательно)')
        self.teacher_combo.currentIndexChanged.connect(self._on_teacher_changed)
        form.addRow('ФИО студента:', self.student_edit)
        form.addRow('Группа:', self.group_edit)
        form.addRow('Полный вариант:', self.variant_edit)
        form.addRow('', self.variant_note)
        form.addRow('Преподаватель:', self.teacher_combo)
        form.addRow('Другое ФИО:', self.custom_teacher_edit)
        form.addRow('Должность:', self.teacher_position_edit)
        form.addRow('Дата выполнения:', self.student_date_edit)
        form.addRow('Дата проверки:', self.teacher_date_edit)
        self._on_teacher_changed()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Подписи остаются пустыми, как в образце преподавателя.'))
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_teacher_changed(self, *_):
        index = self.teacher_combo.currentIndex()
        own = index == len(self.TEACHERS)-1
        self.custom_teacher_edit.setVisible(own)
        if not own:
            self.teacher_position_edit.setText(self.TEACHERS[index][1])

    def set_data(self, data):
        self.student_edit.setText(data.get('student_name', ''))
        self.group_edit.setText(data.get('group', ''))
        self.variant_edit.setText(data.get('variant', ''))
        teacher = data.get('teacher', self.TEACHERS[0][0])
        names = [x[0] for x in self.TEACHERS[:-1]]
        if teacher in names:
            self.teacher_combo.setCurrentIndex(names.index(teacher))
        else:
            self.teacher_combo.setCurrentIndex(len(self.TEACHERS)-1)
            self.custom_teacher_edit.setText(teacher)
        self.teacher_position_edit.setText(data.get('teacher_position') or self.teacher_position_edit.text())
        self.student_date_edit.setText(data.get('date', ''))
        self.teacher_date_edit.setText(data.get('teacher_date', ''))

    def get_data(self):
        teacher = (self.custom_teacher_edit.text().strip()
                   if self.teacher_combo.currentIndex() == len(self.TEACHERS)-1
                   else self.teacher_combo.currentText())
        return {
            'student_name': self.student_edit.text().strip(),
            'group': self.group_edit.text().strip(),
            'variant': self.variant_edit.text().strip(),
            'teacher': teacher,
            'teacher_position': self.teacher_position_edit.text().strip(),
            'date': self.student_date_edit.text().strip(),
            'teacher_date': self.teacher_date_edit.text().strip(),
        }
