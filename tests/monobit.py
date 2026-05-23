import math
from typing import List
from .base import BaseTest

class MonobitTest(BaseTest):
    """
    Частотный тест (Monobit Test).
    Проверяет, равно ли количество нулей и единиц в последовательности.
    """
    
    def run(self, data: List[int]) -> float:
        # 1. Преобразование целых чисел в биты (берем младший бит)
        bits = [x & 1 for x in data]
        n = len(bits)
        if n == 0: return 0.0
        
        # 2. Вычисление суммы S
        # Преобразуем 0 -> -1, 1 -> +1
        s = sum(2 * b - 1 for b in bits)
        
        # 3. Вычисление наблюдаемой статистики S_obs
        s_obs = abs(s) / math.sqrt(n)
        
        # 4. Вычисление p-value
        p_value = math.erfc(s_obs / math.sqrt(2))
        return p_value
    
    def get_name(self) -> str:
        return "Monobit Test (Частотный)"