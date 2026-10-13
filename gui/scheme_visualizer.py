import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import numpy as np


class SchemeVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.create_ui()
        
        self.n_segments = 4
        self.loads = []
        self.support_side = 'right'
        self.l_value = 1.0
        self.P_value = 15
        self.q_value = 15
    
    def create_ui(self):
        layout = QVBoxLayout(self)
        
        self.figure = Figure(figsize=(10, 3), dpi=100, facecolor='#f8f9fa')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(180)
        self.canvas.setMaximumHeight(220)
        
        layout.addWidget(self.canvas)
    
    def update_scheme(self, loads, support_side='right', l_value=1.0, 
                      P_value=15, q_value=15):
        """Обновить схему нагружения"""
        self.loads = loads
        self.support_side = support_side
        self.l_value = l_value
        self.P_value = P_value
        self.q_value = q_value
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#f8f9fa')
        
        total_length = 4
        y_rod = 0
        
        # Рисуем стержень
        ax.plot([0, total_length], [y_rod, y_rod], 'k-', linewidth=3, zorder=5)
        
        # Рисуем опору
        if support_side == 'right':
            self._draw_fixed_support_right(ax, total_length, y_rod)
        else:
            self._draw_fixed_support_left(ax, 0, y_rod)
        
        # Подсчитываем количество нагрузок
        force_count = sum(1 for load in loads if load['type'] == 'force')
        dist_count = sum(1 for load in loads if load['type'] == 'distributed')
        
        # Рисуем сосредоточенные силы
        force_idx = 0
        for load in loads:
            if load['type'] == 'force':
                force_idx += 1
                is_at_free_end = (load['position'] == 0 and support_side == 'right') or \
                                (load['position'] == total_length and support_side == 'left')
                
                if is_at_free_end:
                    self._draw_force_outside(ax, load, y_rod, force_idx, force_count, support_side)
                else:
                    self._draw_concentrated_force(ax, load, y_rod, force_idx, force_count)
        
        # Рисуем распределённые нагрузки
        dist_idx = 0
        for load in loads:
            if load['type'] == 'distributed':
                dist_idx += 1
                self._draw_distributed_load(ax, load, y_rod, dist_idx, dist_count)
        
        # Размерные линии
        self._draw_dimension_lines(ax, total_length, y_rod)
        
        # Настройки
        ax.set_xlim(-1.5, total_length + 1.0)
        ax.set_ylim(-1.2, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Подписи участков
        for i in range(4):
            ax.text(i + 0.5, -0.95, f'{i+1}', 
                   ha='center', fontsize=12, style='italic')
        
        ax.text(total_length + 0.5, y_rod + 0.1, 'z', 
               fontsize=13, style='italic')
        
        self.canvas.draw()
    
    def _draw_fixed_support_right(self, ax, x, y):
        ax.plot([x, x], [y - 0.4, y + 0.4], 'k-', linewidth=2, zorder=6)
        for i in range(8):
            y_start = y + 0.4 - i * 0.1
            y_end = y_start - 0.15
            ax.plot([x, x + 0.15], [y_start, y_end], 'k-', linewidth=1)
    
    def _draw_fixed_support_left(self, ax, x, y):
        ax.plot([x, x], [y - 0.4, y + 0.4], 'k-', linewidth=2, zorder=6)
        for i in range(8):
            y_start = y + 0.4 - i * 0.1
            y_end = y_start - 0.15
            ax.plot([x, x - 0.15], [y_start, y_end], 'k-', linewidth=1)
    
    def _draw_force_outside(self, ax, load, y_rod, idx, total, support_side):
        """Сила P за схемой"""
        x = load['position']
        count = load['count']
        magnitude = count * self.P_value
        direction = load['direction']
        
        # Для опоры слева свободный конец справа (x=4)
        if support_side == 'left':
            if direction == 1:  # вправо
                arrow = FancyArrowPatch((x + 0.1, y_rod), (x + 0.8, y_rod),
                                       arrowstyle='->', mutation_scale=30,
                                       linewidth=3, color='#d32f2f')
                label_x = x + 0.45
            else:  # влево
                arrow = FancyArrowPatch((x - 0.1, y_rod), (x - 0.8, y_rod),
                                       arrowstyle='->', mutation_scale=30,
                                       linewidth=3, color='#d32f2f')
                label_x = x - 0.45
        else:
            # Для опоры справа свободный конец слева (x=0)
            if direction == 1:  # вправо
                arrow = FancyArrowPatch((x - 0.8, y_rod), (x - 0.1, y_rod),
                                       arrowstyle='->', mutation_scale=30,
                                       linewidth=3, color='#d32f2f')
                label_x = x - 0.45
            else:  # влево
                arrow = FancyArrowPatch((x + 0.8, y_rod), (x + 0.1, y_rod),
                                       arrowstyle='->', mutation_scale=30,
                                       linewidth=3, color='#d32f2f')
                label_x = x + 0.45
        
        ax.add_patch(arrow)
        
        if total > 1:
            label = f'{idx}P={magnitude}'
        else:
            label = f'P={magnitude}'
        ax.text(label_x, y_rod + 0.3, label,
               ha='center', fontsize=12, fontweight='bold', color='#d32f2f')
    
    def _draw_concentrated_force(self, ax, load, y_rod, idx, total):
        """Сосредоточенная сила P над стержнем"""
        x = load['position']
        count = load['count']
        magnitude = count * self.P_value
        direction = load['direction']
        
        if direction == 1:  # вправо
            arrow = FancyArrowPatch((x - 0.4, y_rod + 0.5), (x - 0.05, y_rod + 0.5),
                                   arrowstyle='->', mutation_scale=25,
                                   linewidth=2.5, color='#d32f2f')
            label_x = x - 0.2
        else:  # влево
            arrow = FancyArrowPatch((x + 0.4, y_rod + 0.5), (x + 0.05, y_rod + 0.5),
                                   arrowstyle='->', mutation_scale=25,
                                   linewidth=2.5, color='#d32f2f')
            label_x = x + 0.2
        
        ax.add_patch(arrow)
        
        if total > 1:
            label = f'{idx}P={magnitude}'
        else:
            label = f'P={magnitude}'
        ax.text(label_x, y_rod + 0.7, label,
               ha='center', fontsize=11, fontweight='bold', color='#d32f2f')
    
    def _draw_distributed_load(self, ax, load, y_rod, idx, total):
        """Распределённая нагрузка q"""
        start = load['start']
        end = load['end']
        count = load['count']
        intensity = count * self.q_value
        direction = load['direction']
        
        y_top = y_rod + 0.5
        ax.plot([start, end], [y_top, y_top], 'k-', linewidth=1.5)
        
        n_arrows = max(3, int((end - start) * 4))
        for i in range(n_arrows):
            x = start + (end - start) * (i + 0.5) / n_arrows
            
            if direction == 1:  # вправо
                arrow = FancyArrowPatch((x - 0.08, y_top), (x + 0.08, y_top),
                                       arrowstyle='->', mutation_scale=12,
                                       linewidth=1.2, color='#1976d2')
            else:  # влево
                arrow = FancyArrowPatch((x + 0.08, y_top), (x - 0.08, y_top),
                                       arrowstyle='->', mutation_scale=12,
                                       linewidth=1.2, color='#1976d2')
            ax.add_patch(arrow)
        
        if total > 1:
            label = f'{idx}q={intensity}'
        else:
            label = f'q={intensity}'
        ax.text((start + end) / 2, y_top + 0.25, label,
               ha='center', fontsize=11, fontweight='bold', color='#1976d2')
    
    def _draw_dimension_lines(self, ax, total_length, y_rod):
        y_dim = y_rod - 0.5
        ax.plot([0, total_length], [y_dim, y_dim], 'k-', linewidth=0.8)
        
        for i in range(5):
            x = i
            ax.plot([x, x], [y_rod - 0.05, y_dim + 0.05], 'k-', linewidth=0.8)
        
        for i in range(4):
            x_center = i + 0.5
            ax.text(x_center, y_dim - 0.15, 'l',
                   ha='center', fontsize=12, style='italic')