import random
from typing import List, Dict, Any
from .base import BaseGenerator

class MersenneTwister(BaseGenerator):
    """
    Генератор Вихрь Мерсенна (Mersenne Twister).
    Использует встроенный модуль random Python.
    """
    
    def __init__(self, seed: int):
        super().__init__(seed)
        random.seed(seed)
        self._name = "Mersenne Twister"

    def generate(self, n: int) -> List[int]:
        if n <= 0:
            return []
        # Генерируем 32-битные целые числа
        return [random.getrandbits(32) for _ in range(n)]

    def get_info(self) -> Dict[str, Any]:
        return {
            "type": self._name,
            "seed": self.seed,
            "description": "Стандартный генератор Python (MT19937)"
        }