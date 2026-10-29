from typing import List
from .loads import Load

class Rod:
    def __init__(self, total_length: float = 4.0, n_segments: int = 4):
        self.total_length = total_length  # м
        self.n_segments = n_segments
        self.segment_length = total_length / n_segments  # м
        self.loads: List[Load] = []
        self.boundary_N_left = None   # кН
        self.boundary_N_right = None  # кН
        self.E = 2e11                 # Па (200 ГПа)
        self.allowable_sigma = 160e6  # Па (160 МПа)
        self.allowable_W_coeff = 0.002
    
    def add_load(self, load: Load):
        self.loads.append(load)
    
    def set_boundary(self, left=None, right=None):
        self.boundary_N_left = left
        self.boundary_N_right = right
    
    def get_segment_boundaries(self) -> List[float]:
        """Возвращает координаты границ участков [0, l, 2l, 3l, 4l]"""
        return [i * self.segment_length for i in range(self.n_segments + 1)]