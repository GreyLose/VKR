from typing import List, Dict, Any
from .base import BaseGenerator

class XorShift(BaseGenerator):
    """
    Генератор XorShift.
    Быстрый генератор на основе побитовых сдвигов и исключающего ИЛИ.
    """
    
    def __init__(self, seed: int):
        # Seed не может быть 0 для XorShift
        super().__init__(seed if seed != 0 else 1)
        self.state = self.seed
        self._name = "XorShift"

    def generate(self, n: int) -> List[int]:
        if n <= 0:
            return []
        
        result = []
        current = self.state
        
        for _ in range(n):
            # Алгоритм XorShift 32-bit
            current ^= (current << 13)
            current ^= (current >> 17)
            current ^= (current << 5)
            # Маска для 32 бит (0xFFFFFFFF)
            current &= 0xFFFFFFFF 
            result.append(current)
            
        self.state = current
        return result

    def get_info(self) -> Dict[str, Any]:
        return {
            "type": self._name,
            "seed": self.seed,
            "description": "Быстрый побитовый генератор (XorShift32)"
        }