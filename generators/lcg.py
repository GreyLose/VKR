from typing import List, Dict, Any
from .base import BaseGenerator

class LCG(BaseGenerator):
    """
    Линейный конгруэнтный генератор (LCG).
    Формула: X(n+1) = (a * X(n) + c) mod m
    """
    
    def __init__(self, seed: int, a: int = 16807, m: int = 2147483647, c: int = 0):
        super().__init__(seed)
        self.a = a
        self.m = m
        self.c = c
        self._name = "LCG (MINSTD)"

    def generate(self, n: int) -> List[int]:
        if n <= 0:
            return []
        
        result = []
        current = self.state
        
        for _ in range(n):
            current = (self.a * current + self.c) % self.m
            result.append(current)
            
        self.state = current
        return result

    def get_info(self) -> Dict[str, Any]:
        return {
            "type": self._name,
            "seed": self.seed,
            "parameters": {
                "a": self.a,
                "m": self.m,
                "c": self.c
            },
            "description": "Линейный конгруэнтный генератор (Парк-Миллер)"
        }