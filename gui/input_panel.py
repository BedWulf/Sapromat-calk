"""Панель ввода исходных данных + выпадающий список вариантов из БД."""

from __future__ import annotations

import traceback
from typing import List, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QComboBox, QGroupBox, QFormLayout,
                             QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from core.variants_db import VariantData, load_variants


class InputPanel(QWidget):
    """Панель исходных данных.

    Signals:
        variant_selected(object): emitted whenever the user picks a variant
            from the combo box (a VariantData instance) or switches back to
            manual entry (None). The main window uses it to reconfigure the
            scheme editor automatically.
    """

    variant_selected = pyqtSignal(object)

    MANUAL_ITEM_TEXT = "Ввести данные вручную"

    def __init__(self) -> None:
        super().__init__()
        self._variants: List[VariantData] = []
        self._loading_variant: bool = False  # guard against signal loops
        self.create_ui()
        self._load_variants_db()

    # ------------------------------------------------------------------ UI
    def create_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        header = QLabel("Исходные данные")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # ------------------------- База вариантов -------------------------
        variant_group = QGroupBox("Вариант задания")
        variant_layout = QFormLayout()
        variant_layout.setSpacing(10)

        self.variant_combo = QComboBox()
        self.variant_combo.addItem(self.MANUAL_ITEM_TEXT)
        self.variant_combo.setToolTip(
            "Выберите вариант — поля ниже и схема нагружения "
            "будут заполнены автоматически.")
        self.variant_combo.currentIndexChanged.connect(
            self._on_variant_changed)

        variant_layout.addRow("Выберите вариант:", self.variant_combo)
        variant_group.setLayout(variant_layout)
        layout.addWidget(variant_group)

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

    # ------------------------------------------------------------ БД вариантов
    def _load_variants_db(self) -> None:
        """Загрузить варианты из JSON и наполнить комбобокс."""
        try:
            self._variants = load_variants()
        except Exception as exc:  # noqa: BLE001 — показываем пользователю
            traceback.print_exc()
            QMessageBox.warning(
                self, "База вариантов",
                f"Не удалось загрузить базу вариантов:\n{exc}\n"
                "Можно вводить данные вручную.")
            self._variants = []
            return

        # Индексы комбобокса: 0 — ручной ввод, далее i+1 — self._variants[i]
        for var in self._variants:
            self.variant_combo.addItem(f"Вариант {var.variant_id}")

    @pyqtSlot(int)
    def _on_variant_changed(self, index: int) -> None:
        """Обработка выбора варианта: автозаполнение полей + сигнал."""
        if self._loading_variant:
            return

        if index <= 0 or index - 1 >= len(self._variants):
            # Пункт "Ввести данные вручную" — ничего не подставляем
            self.variant_selected.emit(None)
            return

        variant = self._variants[index - 1]
        self._apply_variant_to_fields(variant)
        self.variant_selected.emit(variant)

    def _apply_variant_to_fields(self, variant: VariantData) -> None:
        """Заполнить QLineEdit значениями выбранного варианта."""
        self._loading_variant = True
        try:
            self.P_edit.setText(f"{variant.P:g}")
            self.q_edit.setText(f"{variant.q:g}")
            self.l_edit.setText(f"{variant.l:g}")
            self.sigma_edit.setText(f"{variant.sigma_allow:g}")
            self.E_edit.setText(f"{variant.E:g}")
        finally:
            self._loading_variant = False

    # -------------------------------------------------------------- публичное
    def get_current_variant(self) -> Optional[VariantData]:
        """Вернуть выбранный вариант или None (ручной ввод)."""
        index = self.variant_combo.currentIndex()
        if index <= 0 or index - 1 >= len(self._variants):
            return None
        return self._variants[index - 1]

    def set_manual_mode(self) -> None:
        """Сбросить выбор обратно в режим ручного ввода."""
        self.variant_combo.setCurrentIndex(0)

    # ---------------------------------------------------------------- helpers
    def _on_value_changed(self) -> None:
        """Уведомить родительское окно об изменении значений.

        При выборе варианта из БД схему перестраивает MainWindow через
        сигнал variant_selected — здесь только синхронизация P/q/l
        с редактором схемы при ручном вводе.
        """
        if self._loading_variant:
            return
        try:
            P = float(self.P_edit.text())
            q = float(self.q_edit.text())
            l = float(self.l_edit.text())

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
        """Собрать введённые данные в словарь для расчёта."""
        current_variant = self.get_current_variant()
        return {
            "P": float(self.P_edit.text()) if self.P_edit.text() else 15,
            "q": float(self.q_edit.text()) if self.q_edit.text() else 15,
            "l": float(self.l_edit.text()) if self.l_edit.text() else 1,
            "sigma_allow": float(self.sigma_edit.text()) * 1e6 if self.sigma_edit.text() else 160e6,
            "E": float(self.E_edit.text()) * 1e6 if self.E_edit.text() else 200000e6,
            "W_coeff": float(self.W_coeff_edit.text()) if self.W_coeff_edit.text() else 0.002,
            "shape": self.shape_combo.currentIndex(),
            "variant": current_variant.variant_id if current_variant else "",
        }
