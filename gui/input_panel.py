"""Панель ввода исходных данных + раздельный выбор схемы и данных из БД.

Логика выбора варианта (как в методичке ОмГТУ):
  * "Номер варианта" — готовая комбинация (схема + данные) из `variants`;
  * "Схема нагружения" и "Числовые данные" — независимые комбобоксы,
    позволяют собрать свою комбинацию (например, схема 12 + данные 3);
  * "Своя схема / свои данные" — полный ручной режим: поля P, q, l, [σ], E
    редактируются пользователем, нагрузки расставляются в редакторе схемы.
"""

from __future__ import annotations

import traceback
from typing import List, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QLineEdit, QComboBox, QGroupBox, QFormLayout,
                             QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from core.variants_db import (NumericData, Scheme, VariantData, VariantsDB,
                              load_database)


class InputPanel(QWidget):
    """Панель исходных данных.

    Signals:
        variant_selected(object): emitted whenever the user changes the
            variant selection (a VariantData instance) or switches to full
            manual mode (None). The main window uses it to reconfigure the
            scheme editor automatically.
    """

    variant_selected = pyqtSignal(object)

    MANUAL_VARIANT_TEXT = "Свои данные / своя схема (ручной ввод)"
    MANUAL_SCHEME_TEXT = "Своя схема (расставить нагрузки вручную)"
    MANUAL_DATA_TEXT = "Свои данные (ввести числа вручную)"

    def __init__(self) -> None:
        super().__init__()
        self._db: Optional[VariantsDB] = None
        self._loading_variant: bool = False   # guard against signal loops
        self._composed_variant: Optional[VariantData] = None  # текущий выбранный
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

        # Готовый вариант (схема + данные одной строкой)
        self.variant_combo = QComboBox()
        self.variant_combo.addItem(self.MANUAL_VARIANT_TEXT)
        self.variant_combo.setToolTip(
            "Готовый вариант из базы: автоматически подставятся и числа, "
            "и схема нагружения.")
        self.variant_combo.currentIndexChanged.connect(
            self._on_variant_changed)
        variant_layout.addRow("Номер варианта:", self.variant_combo)

        # Независимый выбор схемы нагружения
        self.scheme_combo = QComboBox()
        self.scheme_combo.setToolTip(
            "Выберите схему нагружения отдельно от числовых данных "
            "(Приложение 2 методички).")
        self.scheme_combo.currentIndexChanged.connect(self._on_scheme_changed)
        variant_layout.addRow("Схема нагружения:", self.scheme_combo)

        # Независимый выбор числовых данных
        self.data_combo = QComboBox()
        self.data_combo.setToolTip(
            "Выберите строку числовых данных P, q, l, [σ], E отдельно "
            "от схемы (Приложение 1 методички).")
        self.data_combo.currentIndexChanged.connect(self._on_data_changed)
        variant_layout.addRow("Числовые данные:", self.data_combo)

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
        """Загрузить базу и наполнить все три комбобокса."""
        try:
            self._db = load_database()
        except Exception as exc:  # noqa: BLE001 — показываем пользователю
            traceback.print_exc()
            QMessageBox.warning(
                self, "База вариантов",
                f"Не удалось загрузить базу вариантов:\n{exc}\n"
                "Можно вводить данные вручную.")
            self._db = None
            return

        self._loading_variant = True
        try:
            for var in self._db.variants:
                self.variant_combo.addItem(f"Вариант {var.variant_id}")
            self.scheme_combo.addItem(self.MANUAL_SCHEME_TEXT)
            for sch in self._db.schemes:
                self.scheme_combo.addItem(
                    f"{sch.name} (закрепление "
                    f"{'слева' if sch.support_side == 'left' else 'справа'})")
            self.data_combo.addItem(self.MANUAL_DATA_TEXT)
            for d in self._db.data_sets:
                self.data_combo.addItem(
                    f"Данные {d.data_id}: P={d.P:g}, q={d.q:g}, l={d.l:g}")
        finally:
            self._loading_variant = False

    # ------------------------------------------------------ слоты комбобоксов
    @pyqtSlot(int)
    def _on_variant_changed(self, index: int) -> None:
        """Выбран готовый вариант: подставляем данные И синхронизируем
        комбобоксы схемы/чисел, затем шлём сигнал в MainWindow.

        Порядок важен: сначала подготавливаем редактор схемы (сигнал с
        данными варианта), только потом синхронизируем раздельные списки —
        их сигналы при этом подавляются флагом _loading_variant.
        """
        if self._loading_variant or self._db is None:
            return
        if index <= 0 or index - 1 >= len(self._db.variants):
            # Пункт "Свои данные / своя схема" — ничего не подставляем
            self.variant_selected.emit(None)
            return

        variant = self._db.variants[index - 1]

        # 1. Числа в поля + сигнал основному окну (обновляет SchemeEditor)
        self._apply_numbers(variant.P, variant.q, variant.l,
                            variant.sigma_allow, variant.E)
        self._composed_variant = variant
        self.variant_selected.emit(variant)

        # 2. Подсветить соответствующие пункты в раздельных списках
        self._loading_variant = True
        try:
            self._sync_combo_to(self.scheme_combo, variant.scheme_id, base=1)
            self._sync_combo_to(self.data_combo, variant.data_id, base=1)
        finally:
            self._loading_variant = False

    @pyqtSlot(int)
    def _on_scheme_changed(self, index: int) -> None:
        """Независимый выбор схемы: пересобираем текущий вариант."""
        if self._loading_variant or self._db is None:
            return
        if index <= 0:
            # Своя схема — передаём управление редактору схемы
            self._composed_variant = None
            self.variant_selected.emit(None)
            return
        scheme = self._db.schemes[index - 1]
        self._emit_composed_variant(scheme=scheme)

    @pyqtSlot(int)
    def _on_data_changed(self, index: int) -> None:
        """Независимый выбор чисел: заполняем поля, пересобираем вариант."""
        if self._loading_variant or self._db is None:
            return
        if index <= 0:
            # Свои данные — поля остаются редактируемыми вручную
            self._composed_variant = None
            self.variant_selected.emit(None)
            return
        data = self._db.data_sets[index - 1]
        self._apply_numbers(data.P, data.q, data.l,
                            data.sigma_allow, data.E)
        self._emit_composed_variant(data=data)

    # ------------------------------------------------------- композиция варианта
    def _current_scheme(self) -> Optional[Scheme]:
        if self._db is None:
            return None
        idx = self.scheme_combo.currentIndex()
        if idx <= 0 or idx - 1 >= len(self._db.schemes):
            return None
        return self._db.schemes[idx - 1]

    def _current_data(self) -> Optional[NumericData]:
        if self._db is None:
            return None
        idx = self.data_combo.currentIndex()
        if idx <= 0 or idx - 1 >= len(self._db.data_sets):
            return None
        return self._db.data_sets[idx - 1]

    def _emit_composed_variant(self,
                               scheme: Optional[Scheme] = None,
                               data: Optional[NumericData] = None) -> None:
        """Собрать вариант из текущей схемы + текущих чисел и послать сигнал.

        Если хотя бы одна из частей выбрана вручную (None) — шлём None,
        чтобы не затирать ручной ввод пользователя.
        """
        scheme = scheme if scheme is not None else self._current_scheme()
        data = data if data is not None else self._current_data()

        if scheme is None or data is None:
            self._composed_variant = None
            self.variant_selected.emit(None)
            return

        composed = VariantData.from_parts(scheme, data)
        self._composed_variant = composed
        self.variant_selected.emit(composed)

    # ---------------------------------------------------------------- helpers
    def _sync_combo_to(self, combo: QComboBox, item_id: str,
                       base: int = 1) -> None:
        """Выбрать в комбобоксе пункт с данным id (без спуска сигналов)."""
        if self._db is None:
            return
        items = (self._db.schemes if combo is self.scheme_combo
                 else self._db.data_sets)
        for i, obj in enumerate(items):
            obj_id = (obj.scheme_id if isinstance(obj, Scheme)
                      else obj.data_id)
            if obj_id == item_id:
                combo.setCurrentIndex(base + i)
                return
        combo.setCurrentIndex(0)

    def _apply_numbers(self, P: float, q: float, l: float,
                       sigma: float, E: float) -> None:
        """Заполнить QLineEdit числовыми значениями."""
        self._loading_variant = True
        try:
            self.P_edit.setText(f"{P:g}")
            self.q_edit.setText(f"{q:g}")
            self.l_edit.setText(f"{l:g}")
            self.sigma_edit.setText(f"{sigma:g}")
            self.E_edit.setText(f"{E:g}")
        finally:
            self._loading_variant = False

    # -------------------------------------------------------------- публичное API
    def get_current_variant(self) -> Optional[VariantData]:
        """Вернуть текущий выбранный вариант или None (ручной режим).

        Это тот же объект, что был передан в последнем сигнале
        variant_selected (готовый вариант из БД либо композиция
        "схема X + данные Y"). В режиме ручного ввода — None.
        """
        return self._composed_variant

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Scheme]:
        if self._db is None:
            return None
        return self._db.get_scheme(scheme_id)

    def set_manual_mode(self) -> None:
        """Сбросить все выборы обратно в режим ручного ввода."""
        self._loading_variant = True
        try:
            self.variant_combo.setCurrentIndex(0)
            self.scheme_combo.setCurrentIndex(0)
            self.data_combo.setCurrentIndex(0)
        finally:
            self._loading_variant = False
        self._composed_variant = None

    # ---------------------------------------------------------------- helpers
    def _on_value_changed(self) -> None:
        """Синхронизация P/q/l с редактором схемы при изменении полей.

        При выборе варианта из БД схему перестраивает MainWindow через
        сигнал variant_selected — здесь только live-синхронизация чисел.
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
