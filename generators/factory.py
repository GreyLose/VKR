from typing import Dict, Type
from .base import BaseGenerator
from .lcg import LCG
from .mersenne_twister import MersenneTwister
from .xorshift import XorShift

# Реестр доступных генераторов
AVAILABLE_GENERATORS: Dict[str, Type[BaseGenerator]] = {
    "lcg": LCG,
    "mersenne": MersenneTwister,
    "xorshift": XorShift
}

def create_generator(gen_type: str, seed: int = 12345) -> BaseGenerator:
    """
    Фабричный метод для создания генератора.
    :param gen_type: Тип генератора ('lcg', 'mersenne', 'xorshift').
    :param seed: Зерно для инициализации.
    :return: Экземпляр генератора.
    """
    gen_class = AVAILABLE_GENERATORS.get(gen_type.lower())
    
    if not gen_class:
        available = ", ".join(AVAILABLE_GENERATORS.keys())
        raise ValueError(f"Неизвестный тип генератора '{gen_type}'. Доступные: {available}")
    
    return gen_class(seed=seed)

def list_generators() -> list:
    """Возвращает список доступных ключей генераторов."""
    return list(AVAILABLE_GENERATORS.keys())