import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.create_ui()
    
    def create_ui(self):
        layout = QVBoxLayout(self)
        
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        
        layout.addWidget(self.canvas)
    
    def plot_N_diagram(self, z_values, N_values, dangerous_z=None, detailed=None):
        """Построить эпюру N(z)"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Каждый непрерывный интервал строится отдельно; на скачке нет
        # вымышленного треугольного распределения силы.
        if detailed:
            for i, interval in enumerate(detailed):
                a,b = interval['z_start'],interval['z_end']
                y0,y1 = interval['N_start'],interval['N_end']
                ax.plot([a,b],[y0,y1],'b-',linewidth=2,
                        label='N(z)' if i == 0 else None)
                ax.fill_between([a,b],[0,0],[y0,y1],alpha=.16,
                                hatch='|',edgecolor='#28629d',facecolor='none')
                if i and abs(detailed[i-1]['N_end']-y0)>1e-8:
                    ax.plot([a,a],[detailed[i-1]['N_end'],y0],
                            'b--',linewidth=1.2)
        else:
            ax.plot(z_values,N_values,'b-',linewidth=2,label='N(z)')
            ax.fill_between(z_values,0,N_values,alpha=.15)
        ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax.set_xlabel('z, м')
        ax.set_ylabel('N, кН')
        ax.set_title('Эпюра продольной силы N(z)')
        ax.grid(True)
        ax.legend()
        
        if dangerous_z is not None:
            ax.axvline(x=dangerous_z, color='r', linestyle='--', label=f'Опасное сечение z={dangerous_z}м')
            ax.legend()
        
        self.canvas.draw()
    
    def plot_W_diagram(self, z_values, W_values):
        """Построить эпюру W(z)"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.plot(z_values, W_values, 'g-', linewidth=2, label='W(z)')
        ax.fill_between(z_values, 0, W_values, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax.set_xlabel('z, м')
        ax.set_ylabel('W, м')
        ax.set_title('Эпюра перемещений W(z)')
        ax.grid(True)
        ax.legend()
        
        self.canvas.draw()
    
    def plot_scheme(self, rod_data):
        """Построить схему нагружения"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Рисуем стержень
        ax.plot([0, rod_data['total_length']], [0, 0], 'k-', linewidth=3)
        
        # Рисуем нагрузки
        for load in rod_data.get('loads', []):
            if load['type'] == 'force':
                ax.annotate('', xy=(load['position'], 0.1), 
                           xytext=(load['position'], 0),
                           arrowprops=dict(arrowstyle='->', color='r', lw=2))
                ax.text(load['position'], 0.15, f"P={load['value']}кН", 
                       ha='center', color='r')
            elif load['type'] == 'distributed':
                ax.plot([load['start'], load['end']], [0.1, 0.1], 'r-', linewidth=2)
                ax.text((load['start']+load['end'])/2, 0.15, f"q={load['value']}кН/м", 
                       ha='center', color='r')
        
        ax.set_xlim(-0.5, rod_data['total_length'] + 0.5)
        ax.set_ylim(-0.5, 0.5)
        ax.set_title('Схема нагружения')
        ax.axis('off')
        
        self.canvas.draw()