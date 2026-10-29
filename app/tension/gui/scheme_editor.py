from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QGroupBox, QPushButton,
                             QRadioButton, QCheckBox, QScrollArea, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from gui.scheme_visualizer import SchemeVisualizer
from core.variants import get_preset_scheme
from core.problem import make_calculator
import math


class SchemeEditor(QWidget):
    model_changed = pyqtSignal()
    def __init__(self, n_segments=4):
        super().__init__()
        self.n_segments = n_segments
        self.auto_boundary = True
        self.preset_number = 2
        self.custom_scheme = False
        self._l_value = 1.0
        self._P_value = 15
        self._q_value = 15
        self._last_boundary_values = None
        self.create_ui()

    def create_ui(self):
        # Главная прокручиваемая область
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок
        header = QLabel("Редактор схемы нагружения")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        main_layout.addWidget(header)

        preset_bar = QHBoxLayout()
        self.custom_scheme_check = QCheckBox("Своя схема (включить ручное редактирование)")
        self.custom_scheme_check.toggled.connect(self.set_custom_scheme)
        self.preset_combo = QComboBox()
        for number in range(1, 31):
            self.preset_combo.addItem(f"Схема № {number}", number)
        self.preset_combo.setCurrentIndex(1)
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        preset_bar.addWidget(QLabel("Схема из приложения 2:"))
        preset_bar.addWidget(self.preset_combo)
        preset_bar.addWidget(self.custom_scheme_check)
        main_layout.addLayout(preset_bar)

        # Визуализация схемы (компактная)
        self.visualizer = SchemeVisualizer()
        self.visualizer.setMinimumHeight(180)
        self.visualizer.setMaximumHeight(220)
        main_layout.addWidget(self.visualizer)

        # Граничные условия
        boundary_group = QGroupBox("Граничные условия")
        boundary_layout = QVBoxLayout()
        boundary_layout.setSpacing(5)

        self.auto_boundary_check = QCheckBox("Граничное условие автоматически по свободному торцу")
        self.auto_boundary_check.setChecked(True)
        self.auto_boundary_check.toggled.connect(self.on_auto_boundary_changed)
        boundary_layout.addWidget(self.auto_boundary_check)

        support_layout = QHBoxLayout()
        support_layout.addWidget(QLabel("Место закрепления:"))
        self.support_left_radio = QRadioButton("Слева (z = 0)")
        self.support_right_radio = QRadioButton("Справа (z = 4l)")
        self.support_right_radio.setChecked(True)
        self.support_group = QButtonGroup(self)
        self.support_group.addButton(self.support_left_radio)
        self.support_group.addButton(self.support_right_radio)
        self.support_left_radio.toggled.connect(self._support_changed)
        self.support_right_radio.toggled.connect(self._support_changed)
        support_layout.addWidget(self.support_left_radio)
        support_layout.addWidget(self.support_right_radio)
        boundary_layout.addLayout(support_layout)

        # Два значения показываются как результат, а не как два поля ввода.
        gu_display = QHBoxLayout()
        gu_display.addWidget(QLabel("N(0) ="))
        self.N0_label = QLabel("—")
        self.N0_label.setStyleSheet("font-weight: bold; color: #1565c0;")
        gu_display.addWidget(self.N0_label)
        gu_display.addSpacing(18)
        gu_display.addWidget(QLabel("N(4l) ="))
        self.N4l_label = QLabel("—")
        self.N4l_label.setStyleSheet("font-weight: bold; color: #1565c0;")
        gu_display.addWidget(self.N4l_label)
        gu_display.addStretch()
        boundary_layout.addLayout(gu_display)

        # Только одно редактируемое условие, определяемое стороной опоры.
        self.manual_boundary_row = QWidget()
        manual_layout = QHBoxLayout(self.manual_boundary_row)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        self.manual_boundary_label = QLabel("N(0), кН:")
        self.manual_boundary_edit = QLineEdit()
        self.manual_boundary_edit.setMaximumWidth(140)
        self.manual_boundary_edit.setPlaceholderText("По свободному концу")
        self.manual_boundary_edit.textChanged.connect(self.update_scheme)
        manual_layout.addWidget(QLabel("Ввести одно условие:"))
        manual_layout.addWidget(self.manual_boundary_label)
        manual_layout.addWidget(self.manual_boundary_edit)
        manual_layout.addStretch()
        boundary_layout.addWidget(self.manual_boundary_row)

        self.boundary_status = QLabel("Второе условие вычисляется из уравнения равновесия.")
        self.boundary_status.setWordWrap(True)
        boundary_layout.addWidget(self.boundary_status)
        boundary_group.setLayout(boundary_layout)
        main_layout.addWidget(boundary_group)

        # Участки (компактные)
        self.segment_widgets = []
        for i in range(self.n_segments):
            segment_widget = self.create_segment_widget(i)
            self.segment_widgets.append(segment_widget)
            main_layout.addWidget(segment_widget)

        # Кнопка сброса
        reset_btn = QPushButton("Сбросить все нагрузки")
        reset_btn.setObjectName("resetButton")
        reset_btn.clicked.connect(self.reset_loads)
        main_layout.addWidget(reset_btn)

        self.on_preset_changed()
        self.set_custom_scheme(False)
        self.on_auto_boundary_changed(True)
        main_layout.addStretch()

        main_scroll.setWidget(main_widget)

        # Внешний layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(main_scroll)

    def create_segment_widget(self, segment_idx):
        group = QGroupBox(f"Участок {segment_idx + 1} (от {segment_idx}l до {segment_idx + 1}l)")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        add_btn = QPushButton("+ Добавить нагрузку")
        add_btn.setObjectName("addButton")
        add_btn.clicked.connect(lambda: self.add_load(segment_idx))
        layout.addWidget(add_btn)

        group.setLayout(layout)
        group.setProperty("segment_idx", segment_idx)

        return group

    def add_load(self, segment_idx):
        group = self.segment_widgets[segment_idx]
        layout = group.layout()

        # Компактная строка нагрузки
        load_row = QHBoxLayout()
        load_row.setSpacing(5)

        type_combo = QComboBox()
        type_combo.addItems(["Сила P", "Нагрузка q"])
        type_combo.setMaximumWidth(120)
        type_combo.currentIndexChanged.connect(lambda: self.update_scheme())

        dir_combo = QComboBox()
        dir_combo.addItems(["→", "←"])
        dir_combo.setMaximumWidth(60)
        dir_combo.currentIndexChanged.connect(lambda: self.update_scheme())

        count_edit = QLineEdit("1")
        count_edit.setPlaceholderText("кол")
        count_edit.setMaximumWidth(60)
        count_edit.textChanged.connect(lambda: self.update_scheme())

        # В пользовательской схеме каждую нагрузку можно разместить произвольно.
        pos_edit = QLineEdit(str(0 if segment_idx == 0 and self.support_right_radio.isChecked()
                                  else 4 if segment_idx == 3 and self.support_left_radio.isChecked()
                                  else segment_idx + 1))
        start_edit = QLineEdit(str(segment_idx))
        end_edit = QLineEdit(str(segment_idx + 1))
        for field in (pos_edit,start_edit,end_edit):
            field.setMaximumWidth(55)
            field.textChanged.connect(self.update_scheme)
        pos_label=QLabel('z/l:')
        start_label=QLabel('от/l:')
        end_label=QLabel('до/l:')
        for label, field in ((pos_label,pos_edit),(start_label,start_edit),(end_label,end_edit)):
            label.setToolTip('Координаты в долях l, например 1.5')

        def sync_coordinate_fields():
            is_force=(type_combo.currentIndex()==0)
            for widget in (pos_label,pos_edit):
                widget.setVisible(is_force)
            for widget in (start_label,start_edit,end_label,end_edit):
                widget.setVisible(not is_force)
            self.update_scheme()
        type_combo.currentIndexChanged.connect(sync_coordinate_fields)

        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("removeButton")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_load(segment_idx, load_row, 
                                                            type_combo, dir_combo, count_edit))

        load_row.addWidget(QLabel("Тип:"), 0)
        load_row.addWidget(type_combo, 1)
        load_row.addWidget(QLabel("Напр:"), 0)
        load_row.addWidget(dir_combo, 0)
        load_row.addWidget(QLabel("Кол:"), 0)
        load_row.addWidget(count_edit, 0)
        for widget in (pos_label,pos_edit,start_label,start_edit,end_label,end_edit):
            load_row.addWidget(widget,0)
        load_row.addWidget(remove_btn, 0)
        load_row.addStretch()

        layout.addLayout(load_row)

        if not hasattr(group, 'load_widgets'):
            group.load_widgets = []
        group.load_widgets.append({
            'type': type_combo,
            'direction': dir_combo,
            'count': count_edit,
            'pos':pos_edit, 'start':start_edit, 'end':end_edit,
            'row': load_row
        })

        sync_coordinate_fields()

    def remove_load(self, segment_idx, load_row, type_combo, dir_combo, count_edit):
        group = self.segment_widgets[segment_idx]

        for i, widget in enumerate(group.load_widgets):
            if widget['count'] == count_edit:
                group.load_widgets.pop(i)
                break

        layout = group.layout()
        layout.removeItem(load_row)
        while load_row.count():
            item=load_row.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self.update_scheme()

    def _support_side(self):
        return 'left' if self.support_left_radio.isChecked() else 'right'

    def _free_boundary_key(self):
        return 'N_right' if self._support_side() == 'left' else 'N_left'

    def _update_boundary_controls(self):
        # Стандартная схема полностью определяет закрепление и граничное условие.
        standard = not self.custom_scheme
        self.auto_boundary_check.setEnabled(not standard)
        if standard and not self.auto_boundary_check.isChecked():
            self.auto_boundary_check.setChecked(True)
        self.auto_boundary = standard or self.auto_boundary_check.isChecked()
        label = 'N(4l), кН:' if self._support_side() == 'left' else 'N(0), кН:'
        self.manual_boundary_label.setText(label)
        self.manual_boundary_row.setVisible(self.custom_scheme and not self.auto_boundary)

    def _seed_manual_values(self):
        """Подстановка ожидаемого условия со свободного торца, без фиктивного нуля."""
        try:
            values = make_calculator(self.get_scheme(), self._P_value, self._q_value,
                                     l=self._l_value, support=self._support_side()).boundary_values()
            self._last_boundary_values = values
            field = self.manual_boundary_edit
            was_blocked = field.blockSignals(True)
            try:
                field.setText(f"{values[self._free_boundary_key()]:.10g}")
            finally:
                field.blockSignals(was_blocked)
        except (ValueError, TypeError, OverflowError):
            self.manual_boundary_edit.clear()

    def _support_changed(self, checked):
        if not checked:
            return
        # Нельзя сохранять N(0) при переходе на левую заделку и наоборот.
        self._update_boundary_controls()
        if self.custom_scheme and not self.auto_boundary:
            self._seed_manual_values()
        self.update_scheme()

    def on_auto_boundary_changed(self, checked):
        self._update_boundary_controls()
        if self.custom_scheme and not self.auto_boundary:
            self._seed_manual_values()
        self.update_scheme()

    def set_custom_scheme(self, checked):
        self.custom_scheme = checked
        self.preset_combo.setEnabled(not checked)
        for group in self.segment_widgets:
            group.setEnabled(checked)
        self.support_left_radio.setEnabled(checked)
        self.support_right_radio.setEnabled(checked)
        if not checked:
            # Возвращение к стандартной схеме всегда возвращает автоматический режим.
            self.auto_boundary_check.setChecked(True)
            self.on_preset_changed()
        self._update_boundary_controls()
        self.update_scheme()

    def on_preset_changed(self, *_):
        self.preset_number = self.preset_combo.currentData() or 1
        if not self.custom_scheme:
            support, _ = get_preset_scheme(self.preset_number, self._l_value)
            self.support_left_radio.setChecked(support == 'left')
            self.support_right_radio.setChecked(support == 'right')
        self._update_boundary_controls()
        self.update_scheme()

    def get_boundary_conditions(self) -> dict:
        """Единственное заданное условие всегда относится к свободному торцу.

        При стандартной схеме оно всегда выводится из торцевой силы.
        При пользовательской схеме допускается ввод одного значения по
        автоматически выбранному концу. Противоречие нагрузкам отлавливает
        make_calculator() до вычисления эпюры.
        """
        key = self._free_boundary_key()
        if self.custom_scheme and not self.auto_boundary:
            raw = self.manual_boundary_edit.text().strip().replace(',', '.')
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError('Введите числовое условие ' + self.manual_boundary_label.text()) from exc
            if not math.isfinite(value):
                raise ValueError('Граничное условие должно быть конечным числом')
        else:
            value = make_calculator(self.get_scheme(), self._P_value,
                                    self._q_value, l=self._l_value,
                                    support=self._support_side()).boundary_values()[key]
        return {'N_left': value if key == 'N_left' else None,
                'N_right': value if key == 'N_right' else None}

    def update_scheme(self):
        self.model_changed.emit()
        try:
            scheme = self.get_scheme()
            boundary = self.get_boundary_conditions()
            support_side = 'left' if self.support_left_radio.isChecked() else 'right'
            calc = make_calculator(scheme, self._P_value, self._q_value,
                                   l=self._l_value, support=support_side,
                                   boundary=boundary)
            values = calc.boundary_values()
            self._last_boundary_values = values
            self.N0_label.setText(f"{values['N_left']:.3f} кН")
            self.N4l_label.setText(f"{values['N_right']:.3f} кН")
            given = ('автоматически по свободному торцу' if self.auto_boundary
                     else 'по одному введённому Г.У. (' + self.manual_boundary_label.text().replace(', кН:', '') + ')')
            reaction = calc.support_reaction()
            self.boundary_status.setText(
                f'Оба Г.У. согласованы с равновесием ({given}). '
                f'Реакция опоры Rz = {reaction:.3f} кН.')
            self.boundary_status.setStyleSheet('color: #267341;')
            all_loads = [load for group in scheme for load in group]
            self.visualizer.update_scheme(all_loads,support_side,
                                           self._l_value,self._P_value,self._q_value)
        except (ValueError, TypeError, OverflowError) as exc:
            # При наборе значения поле может временно быть пустым: сообщаем
            # о проблеме вместо аварийного завершения сигнального обработчика.
            self.N0_label.setText('—')
            self.N4l_label.setText('—')
            self.boundary_status.setText('Проверьте данные: ' + str(exc))
            self.boundary_status.setStyleSheet('color: #c62828;')

    def set_l_value(self, l_value):
        self._l_value = l_value
        self.update_scheme()

    def set_P_value(self, P_value):
        self._P_value = P_value
        self.update_scheme()

    def set_q_value(self, q_value):
        self._q_value = q_value
        self.update_scheme()

    def reset_loads(self):
        for group in self.segment_widgets:
            if hasattr(group, 'load_widgets'):
                for widget in group.load_widgets[:]:
                    self.remove_load(group.property("segment_idx"), 
                                   widget['row'], widget['type'], 
                                   widget['direction'], widget['count'])
        self.update_scheme()

    def get_scheme(self) -> list:
        if not self.custom_scheme:
            return get_preset_scheme(self.preset_number, self._l_value)[1]
        scheme = []
        for segment_idx, group in enumerate(self.segment_widgets):
            segment_loads=[]
            for load in getattr(group,'load_widgets',[]):
                try:
                    count=float(load['count'].text().replace(',','.'))
                except ValueError as exc:
                    raise ValueError('Введите числовой множитель нагрузки') from exc
                if not math.isfinite(count) or count<0:
                    raise ValueError('Множитель нагрузки должен быть конечным и неотрицательным')
                if count==0:
                    continue
                direction=1 if load['direction'].currentIndex()==0 else -1
                l=self._l_value
                if load['type'].currentIndex()==0:
                    try:
                        pos=float(load['pos'].text().replace(',','.'))
                    except ValueError as exc:
                        raise ValueError('Координата силы z/l должна быть числом') from exc
                    if not math.isfinite(pos) or not 0 <= pos <= 4:
                        raise ValueError('Координата силы должна быть в пределах 0…4l')
                    segment_loads.append({'type':'force', 'direction':direction,
                                         'count':count,'position':pos*l,'segment':segment_idx})
                else:
                    try:
                        a=float(load['start'].text().replace(',','.'))
                        b=float(load['end'].text().replace(',','.'))
                    except ValueError as exc:
                        raise ValueError('Границы распределённой нагрузки должны быть числами') from exc
                    if not all(map(math.isfinite,(a,b))) or not 0<=a<b<=4:
                        raise ValueError('Нужно указать 0 ≤ начало < конец ≤ 4 (в долях l)')
                    segment_loads.append({'type':'distributed','direction':direction,
                                         'count':count,'start':a*l,'end':b*l,
                                         'segment':segment_idx})
            scheme.append(segment_loads)
        return scheme
