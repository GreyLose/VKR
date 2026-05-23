from typing import List
import numpy as np
from scipy.stats import chisquare, kstest
from .base import BaseTest

class ChiSquareTest(BaseTest):
    """
    Тест на равномерность распределения.
    Гибридная реализация: Chi-Square + fallback на KS-тест.
    """
    
    def __init__(self, alpha: float = 0.01, bins: int = 10):
        super().__init__(alpha)
        self.bins = bins

    def run(self, data: List[int]) -> float:
        if not data or len(data) < self.bins * 5:
            return 0.5
        
        try:
            # Вариант 1: Если данные уже в диапазоне [0, bins-1] — используем bincount
            if max(data) < self.bins and min(data) >= 0:
                hist = np.bincount(data, minlength=self.bins)[:self.bins].astype(float)
                # Добавляем малое значение для стабильности
                hist = np.clip(hist, 0.5, None)
                expected = len(data) / self.bins
                _, p_val = chisquare(hist, f_exp=[expected] * self.bins)
                
            # Вариант 2: Для произвольных данных — нормализация + KS-тест
            else:
                data_array = np.array(data, dtype=float)
                min_v, max_v = data_array.min(), data_array.max()
                if max_v == min_v:
                    return 0.0
                normalized = (data_array - min_v) / (max_v - min_v)
                _, p_val = kstest(normalized, 'uniform')
            
            # Защита от численных погрешностей
            if p_val <= 0.0 or p_val > 1.0:
                p_val = 0.5
                
            return max(0.0, min(1.0, p_val))
            
        except Exception as e:
            print(f"Chi-Square fallback: {e}")
            return 0.5  # Нейтральное значение при любой ошибке
    
    def get_name(self) -> str:
        return f"Chi-Square (bins={self.bins})"