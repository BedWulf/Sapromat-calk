from .standards import round_to_standard
import math

class SectionSelector:
    @staticmethod
    def from_strength(N_max_kN: float, sigma_allow_Pa: float, shape: str) -> dict:
        """Подбор сечения по прочности"""
        N_max_N = N_max_kN * 1e3  # кН → Н
        F_min = N_max_N / sigma_allow_Pa  # м²
        
        if shape == "square":
            a = math.sqrt(F_min)
            a_std = round_to_standard(a)
            return {"a": a_std, "F": a_std**2, "shape": "square"}
        
        elif shape == "rectangle_2_1":  # h = 2b
            b = math.sqrt(F_min / 2)
            b_std = round_to_standard(b)
            h_std = 2 * b_std
            return {"b": b_std, "h": h_std, "F": b_std * h_std, "shape": "rectangle_2_1"}
        
        elif shape == "circle":
            d = math.sqrt(4 * F_min / math.pi)
            d_std = round_to_standard(d)
            return {"d": d_std, "F": math.pi * d_std**2 / 4, "shape": "circle"}
        
        else:
            raise ValueError(f"Неизвестная форма сечения: {shape}")
    
    @staticmethod
    def from_stiffness(W_max_m: float, W_allow_coeff: float, l_m: float, 
                       E_Pa: float, N_max_kN: float, shape: str) -> dict:
        """Подбор сечения по жёсткости"""
        # [W] = 0.002 * l
        W_allow = W_allow_coeff * l_m
        
        # W_max = N_max * L / (E * F)  (упрощённо)
        # F_min = N_max * L / (E * W_allow)
        N_max_N = N_max_kN * 1e3
        L_total = 4 * l_m  # полная длина стержня
        
        F_min = N_max_N * L_total / (E_Pa * W_allow)
        
        if shape == "square":
            a = math.sqrt(F_min)
            a_std = round_to_standard(a)
            return {"a": a_std, "F": a_std**2, "shape": "square"}
        
        elif shape == "rectangle_2_1":
            b = math.sqrt(F_min / 2)
            b_std = round_to_standard(b)
            h_std = 2 * b_std
            return {"b": b_std, "h": h_std, "F": b_std * h_std, "shape": "rectangle_2_1"}
        
        elif shape == "circle":
            d = math.sqrt(4 * F_min / math.pi)
            d_std = round_to_standard(d)
            return {"d": d_std, "F": math.pi * d_std**2 / 4, "shape": "circle"}
        
        else:
            raise ValueError(f"Неизвестная форма сечения: {shape}")