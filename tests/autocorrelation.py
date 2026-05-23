import math
from typing import List
from .base import BaseTest

class AutocorrelationTest(BaseTest):
    """
    Автокорреляционный тест.
    Проверяет, являются ли сдвинутые версии последовательности некоррелированными.
    """
    
    def __init__(self, alpha: float = 0.01, shift: int = 1):
        super().__init__(alpha)
        self.shift = shift # Сдвиг (lag)

    def run(self, data: List[int]) -> float:
        bits = [x & 1 for x in data]
        n = len(bits)
        d = self.shift
        
        if n <= d: return 1.0
        
        # 1. XOR исходной последовательности со сдвинутой
        # Считаем количество единиц в результате XOR (A_d)
        a_d = 0
        for i in range(n - d):
            if bits[i] != bits[i + d]:
                a_d += 1
                
        # 2. Вычисление статистики
        e_a_d = (n - d) / 2.0
        numerator = a_d - e_a_d
        denominator = math.sqrt(n - d) / 2.0
        
        if denominator == 0: return 0.0
            
        # 3. p-value
        p_value = math.erfc(abs(numerator) / (denominator * math.sqrt(2)))
        return p_value
    
    def get_name(self) -> str:
        return f"Autocorrelation (d={self.shift})"