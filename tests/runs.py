import math
from typing import List
from .base import BaseTest

class RunsTest(BaseTest):
    """
    Тест на серии (Runs Test).
    Определяет, соответствует ли количество серий (последовательностей одинаковых битов)
    ожидаемому для случайной последовательности.
    """
    
    def run(self, data: List[int]) -> float:
        bits = [x & 1 for x in data]
        n = len(bits)
        if n == 0: return 0.0
        
        # 1. Вычисление доли единиц (pi)
        pi = sum(bits) / n
        
        # 2. Предварительная проверка
        if abs(pi - 0.5) >= (2.0 / math.sqrt(n)):
            return 0.0 # Последовательность явно не случайна
        
        # 3. Подсчет количества серий (V)
        runs_count = 1
        for i in range(1, n):
            if bits[i] != bits[i-1]:
                runs_count += 1
        
        # 4. Вычисление p-value
        numerator = abs(runs_count - 2.0 * n * pi * (1 - pi))
        denominator = 2.0 * math.sqrt(2.0 * n) * pi * (1 - pi)
        
        if denominator == 0: return 0.0
            
        p_value = math.erfc(numerator / denominator)
        return p_value
    
    def get_name(self) -> str:
        return "Runs Test (Серии)"