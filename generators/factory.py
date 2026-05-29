from typing import Dict, Type
from .base import BaseGenerator
from .lcg import LCG
from .mersenne_twister import MersenneTwister
from .xorshift import XorShift
from .true_rng import TrueRNG

# Реестр доступных генераторов
AVAILABLE_GENERATORS: Dict[str, Type[BaseGenerator]] = {
    "lcg": LCG,
    "mersenne": MersenneTwister,
    "xorshift": XorShift,
    "true_rng": TrueRNG
}

def create_generator(gen_type: str, seed: int = 12345) -> BaseGenerator:
    """
    Фабричный метод для создания генератора.
    :param gen_type: Тип генератора ('lcg', 'mersenne', 'xorshift', 'true_rng').
    :param seed: Зерно для инициализации.
    :return: Экземпляр генератора.
    """
    gen_class = AVAILABLE_GENERATORS.get(gen_type.lower())
    
    if not gen_class:
        available = ", ".join(AVAILABLE_GENERATORS.keys())
        raise ValueError(f"Неизвестный тип генератора '{gen_type}'. Доступные: {available}")
    
    # TrueRNG не использует seed, остальные требуют его явно
    if gen_type == "true_rng":
        return gen_class()
    
    return gen_class(seed=seed)

def list_generators() -> list:
    """Возвращает список доступных ключей генераторов."""
    return list(AVAILABLE_GENERATORS.keys())