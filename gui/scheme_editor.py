from __future__ import annotations

import contextlib
from typing import List, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QLineEdit, QGroupBox, QPushButton,
                             QRadioButton, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt
from gui.scheme_visualizer import SchemeVisualizer

from core.variants_db import VariantData


class SchemeEditor(QWidget):
    def __init__(self, n_segments=4):
        super().__init__()
        self.n_segments = n_segments
        self.auto_boundary = True
        self._l_value = 1.0
        self._P_value = 15
        self._q_value = 15
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

        # Визуализация схемы (компактная)
        self.visualizer = SchemeVisualizer()
        self.visualizer.setMinimumHeight(180)
        self.visualizer.setMaximumHeight(220)
        main_layout.addWidget(self.visualizer)

        # Граничные условия
        boundary_group = QGroupBox("Граничные условия")
        boundary_layout = QVBoxLayout()
        boundary_layout.setSpacing(5)

        self.auto_boundary_check = QCheckBox("Автоматически определять по схеме (рекомендуется)")
        self.auto_boundary_check.setChecked(True)
        self.auto_boundary_check.toggled.connect(self.on_auto_boundary_changed)
        boundary_layout.addWidget(self.auto_boundary_check)

        support_layout = QHBoxLayout()
        support_layout.addWidget(QLabel("Место закрепления:"))

        self.support_left_radio = QRadioButton("Слева (x = 0)")
        self.support_right_radio = QRadioButton("Справа (x = 4l)")
        self.support_right_radio.setChecked(True)

        self.support_left_radio.toggled.connect(self.update_scheme)
        self.support_right_radio.toggled.connect(self.update_scheme)

        support_layout.addWidget(self.support_left_radio)
        support_layout.addWidget(self.support_right_radio)
        boundary_layout.addLayout(support_layout)

        # Поля ГУ (только для отображения)
        gu_display = QHBoxLayout()
        gu_display.addWidget(QLabel("N(0) ="))
        self.N0_label = QLabel("0 кН")
        self.N0_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        gu_display.addWidget(self.N0_label)

        gu_display.addSpacing(20)

        gu_display.addWidget(QLabel("N(4l) ="))
        self.N4l_label = QLabel("0 кН")
        self.N4l_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        gu_display.addWidget(self.N4l_label)

        boundary_layout.addLayout(gu_display)
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
        load_row.addWidget(remove_btn, 0)
        load_row.addStretch()

        layout.addLayout(load_row)

        if not hasattr(group, 'load_widgets'):
            group.load_widgets = []
        group.load_widgets.append({
            'type': type_combo,
            'direction': dir_combo,
            'count': count_edit,
            'row': load_row
        })

        self.update_scheme()

    def remove_load(self, segment_idx, load_row, type_combo, dir_combo, count_edit):
        group = self.segment_widgets[segment_idx]

        for i, widget in enumerate(group.load_widgets):
            if widget['count'] == count_edit:
                group.load_widgets.pop(i)
                break

        layout = group.layout()
        layout.removeItem(load_row)
        type_combo.deleteLater()
        dir_combo.deleteLater()
        count_edit.deleteLater()

        self.update_scheme()

    def on_auto_boundary_changed(self, checked):
        self.auto_boundary = checked
        self.update_scheme()

    def get_boundary_conditions(self) -> dict:
        """Автоматическое определение ГУ по схеме"""
        if self.auto_boundary:
            support_left = self.support_left_radio.isChecked()
            scheme = self.get_scheme()

            # Собираем все нагрузки
            all_loads = []
            for segment_loads in scheme:
                all_loads.extend(segment_loads)

            if support_left:
                # Опора слева → N(0) = 0
                N_right = 0.0
                for load in all_loads:
                    if load['type'] == 'force' and abs(load['position'] - 4 * self._l_value) < 0.01:
                        N_right -= load['count'] * self._P_value * load['direction']
                return {"N_left": 0.0, "N_right": N_right}
            else:
                # Опора справа → N(4l) = 0
                N_left = 0.0
                for load in all_loads:
                    if load['type'] == 'force' and abs(load['position']) < 0.01:
                        # Сила влево (direction=-1) → растяжение → N положительна
                        N_left -= load['count'] * self._P_value * load['direction']
                return {"N_left": N_left, "N_right": 0.0}
        else:
            try:
                N0 = float(self.N0_edit.text()) if self.N0_edit.text() else 0.0
            except ValueError:
                N0 = 0.0
            try:
                N4l = float(self.N4l_edit.text()) if self.N4l_edit.text() else 0.0
            except ValueError:
                N4l = 0.0
            return {"N_left": N0, "N_right": N4l}

    def update_scheme(self):
        scheme = self.get_scheme()

        all_loads = []
        for segment_loads in scheme:
            all_loads.extend(segment_loads)

        support_side = 'left' if self.support_left_radio.isChecked() else 'right'

        # Обновляем отображение ГУ
        boundary = self.get_boundary_conditions()
        if boundary["N_left"] is not None:
            self.N0_label.setText(f"{boundary['N_left']:.1f} кН")
            self.N4l_label.setText("—")
        else:
            self.N0_label.setText("—")
            self.N4l_label.setText(f"{boundary['N_right']:.1f} кН")

        self.visualizer.update_scheme(
            all_loads, 
            support_side, 
            self._l_value,
            self._P_value,
            self._q_value
        )

    def set_l_value(self, l_value):
        self._l_value = l_value
        self.update_scheme()

    def set_P_value(self, P_value):
        self._P_value = P_value
        self.update_scheme()

    def set_q_value(self, q_value):
        self._q_value = q_value
        self.update_scheme()

    # ------------------------------------------------------ загрузка варианта
    @contextlib.contextmanager
    def _batch_updates(self):
        """Временно отключить перерисовку схемы (для пакетных изменений)."""
        original = self.visualizer.update_scheme
        self.visualizer.update_scheme = lambda *a, **k: None  # type: ignore[assignment]
        try:
            yield
        finally:
            self.visualizer.update_scheme = original  # type: ignore[assignment]
            self.update_scheme()

    def load_variant_scheme(self, variant: Optional[VariantData]) -> None:
        """Программно сконфигурировать редактор по данным варианта из БД.

        Очищает текущие нагрузки, устанавливает сторону закрепления и
        добавляет нагрузки из массива `loads` выбранного варианта, вызывая
        существующую логику add_load.

        Args:
            variant: данные варианта (core.variants_db.VariantData) или None —
                     в этом случае только сброс нагрузок (ручной режим).
        """
        with self._batch_updates():
            # 1. Очистить все текущие нагрузки
            self.reset_loads()

            if variant is None:
                return

            # 2. Граничные условия: сторона закрепления (Приложение 3)
            if variant.support_side == "left":
                self.support_left_radio.setChecked(True)
            else:
                self.support_right_radio.setChecked(True)

            # 3. Числовые параметры стержня
            self._P_value = variant.P
            self._q_value = variant.q
            self._l_value = variant.l

            # 4. Нагрузки: segment в JSON нумеруется с 1, виджеты — с 0
            for entry in variant.loads:
                segment_idx = int(entry.segment) - 1
                if not 0 <= segment_idx < self.n_segments:
                    continue  # защита от некорректных данных в БД

                self.add_load(segment_idx)
                group = self.segment_widgets[segment_idx]
                widget = group.load_widgets[-1]  # только что добавленная строка

                # Тип: индекс 0 = "Сила P", 1 = "Нагрузка q"
                type_index = 0 if entry.load_type == "force" else 1
                widget["type"].setCurrentIndex(type_index)

                # Направление: индекс 0 = "→" (direction=1), 1 = "←" (direction=-1)
                dir_index = 0 if entry.direction == 1 else 1
                widget["direction"].setCurrentIndex(dir_index)

                # Кратность (1 -> P/q, 2 -> 2P/2q ...)
                widget["count"].setText(str(int(entry.count)))


    def reset_loads(self):
        for group in self.segment_widgets:
            if hasattr(group, 'load_widgets'):
                for widget in group.load_widgets[:]:
                    self.remove_load(group.property("segment_idx"), 
                                   widget['row'], widget['type'], 
                                   widget['direction'], widget['count'])
        self.update_scheme()

    def get_scheme(self) -> list:
        scheme = []
        support_left = self.support_left_radio.isChecked()

        for segment_idx, group in enumerate(self.segment_widgets):
            segment_loads = []

            if hasattr(group, 'load_widgets'):
                for load in group.load_widgets:
                    load_type = load["type"].currentIndex()

                    try:
                        count = int(load["count"].text())
                    except ValueError:
                        count = 1

                    if count == 0:
                        continue

                    direction = 1 if load["direction"].currentIndex() == 0 else -1

                    l = self._l_value
                    start = segment_idx * l
                    end = (segment_idx + 1) * l

                    if load_type == 0:  # Сила P
                        # Логика позиции силы:
                        # - Если опора справа и сила на участке 1 → position = 0 (свободный конец)
                        # - Если опора слева и сила на участке 4 → position = 4l (свободный конец)
                        # - Иначе → position = end (конец участка)
                        if not support_left and segment_idx == 0:
                            position = 0.0
                        elif support_left and segment_idx == self.n_segments - 1:
                            position = 4 * l
                        else:
                            position = end

                        segment_loads.append({
                            "type": "force",
                            "direction": direction,
                            "count": count,
                            "position": position,
                            "segment": segment_idx
                        })
                    elif load_type == 1:  # Нагрузка q
                        segment_loads.append({
                            "type": "distributed",
                            "direction": direction,
                            "count": count,
                            "start": start,
                            "end": end,
                            "segment": segment_idx
                        })

            scheme.append(segment_loads)

        return scheme