import math
from typing import List, Tuple
from scipy import stats
import numpy as np
from .base import BaseTest

class MonobitTest(BaseTest):
    """
    Monobit Test (Частотный тест).
    Проверяет, равно ли количество единиц и нулей в последовательности.
    """
    
    def run(self, bits: List[int]) -> Tuple[float, float, bool]:
        n = len(bits)
        if n == 0:
            return 0.0, 0.0, False
            
        # Сумма (2*b - 1) дает +1 для единицы и -1 для нуля
        s = sum(2 * b - 1 for b in bits)
        s_obs = abs(s) / math.sqrt(n)
        
        # Вычисление p-value через дополнительную функцию ошибок
        p_value = math.erfc(s_obs / math.sqrt(2))
        
        passed = p_value >= self.alpha
        return s_obs, p_value, passed

class RunsTest(BaseTest):
    """
    Runs Test (Тест на серии).
    Проверяет, соответствует ли количество серий (последовательностей одинаковых битов)
    ожидаемому для случайной последовательности.
    """
    
    def run(self, bits: List[int]) -> Tuple[float, float, bool]:
        n = len(bits)
        if n == 0:
            return 0.0, 0.0, False
            
        pi = sum(bits) / n
        
        # Предварительная проверка частоты
        if abs(pi - 0.5) >= 2 / math.sqrt(n):
            return 0.0, 0.0, False
            
        # Подсчет количества серий
        runs = 1
        for i in range(1, n):
            if bits[i] != bits[i-1]:
                runs += 1
                
        numerator = abs(runs - 2 * n * pi * (1 - pi))
        denominator = 2 * math.sqrt(2 * n) * pi * (1 - pi)
        
        if denominator == 0:
            return 0.0, 0.0, False
            
        p_value = math.erfc(numerator / denominator)
        passed = p_value >= self.alpha
        return runs, p_value, passed

class ChiSquareTest(BaseTest):
    """
    Chi-Square Test (Хи-квадрат тест на равномерность).
    Проверяет, равномерно ли распределены значения в последовательности.
    """
    
    def run(self, sequence: List[int]) -> Tuple[float, float, bool]:
        if not sequence:
            return 0.0, 0.0, False
            
        # Разбиваем диапазон значений на 10 интервалов (bins)
        hist, _ = np.histogram(sequence, bins=10)
        
        # Используем scipy для расчета p-value
        # null hypothesis: данные распределены равномерно
        _, p_value = stats.chisquare(hist)
        
        passed = p_value >= self.alpha
        return hist[0], p_value, passed # Возвращаем первую ячейку гистограммы как пример статистики