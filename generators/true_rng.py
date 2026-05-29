import os
import struct
from typing import List, Dict, Any
from .base import BaseGenerator

class TrueRNG(BaseGenerator):
    """Генератор на основе энтропии ОС (недетерминированный)"""
    
    def __init__(self):
        """Инициализация без seed - используем аппаратную энтропию"""
        # Не вызываем super().__init__(), так как TrueRNG не использует seed
        pass
    
    def generate(self, n: int) -> List[int]:
        """
        Генерация последовательности из n 32-битных целых чисел
        с использованием энтропии операционной системы.
        """
        if n <= 0:
            raise ValueError("Длина последовательности должна быть > 0")
        
        # os.urandom() автоматически использует криптографически стойкий источник энтропии
        raw_bytes = os.urandom(n * 4)  # 4 байта на каждое 32-битное число
        return list(struct.unpack(f'<{n}I', raw_bytes))  # '<' = little-endian, 'I' = unsigned int
    
    def get_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о генераторе.
        """
        return {
            "name": "TrueRNG",
            "description": "Генератор на основе энтропии операционной системы",
            "deterministic": False,
            "seed_required": False,
            "period": "N/A (истинная случайность)",
            "speed": "Зависит от ОС (~10-30 МБ/с)",
            "cryptographically_secure": True
        }