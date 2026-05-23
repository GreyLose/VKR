from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseGenerator(ABC):
    """
    Абстрактный базовый класс для всех генераторов случайных чисел.
    Гарантирует единый интерфейс для системы тестирования.
    """
    
    def __init__(self, seed: int):
        """
        Инициализация генератора.
        :param seed: Начальное значение (зерно).
        """
        self.seed = seed
        self.state = seed

    @abstractmethod
    def generate(self, n: int) -> List[int]:
        """
        Генерирует последовательность из n целых чисел.
        :param n: Длина последовательности.
        :return: Список целых чисел.
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Возвращает метаданные о генераторе (название, параметры, период).
        Используется для логирования и отображения в UI.
        """
        pass
    
    def reset(self):
        """Сброс состояния генератора к начальному seed."""
        self.state = self.seed