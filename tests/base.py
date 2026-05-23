from abc import ABC, abstractmethod
from typing import List

class BaseTest(ABC):
    """
    Абстрактный базовый класс для всех статистических тестов.
    """
    
    def __init__(self, alpha: float = 0.01):
        """
        :param alpha: Уровень значимости (по умолчанию 0.01).
        """
        self.alpha = alpha

    @abstractmethod
    def run(self, data: List[int]) -> float:
        """
        Запуск теста.
        :param data: Список целых чисел (последовательность).
        :return: p-value (вероятность того, что последовательность случайна).
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Возвращает название теста."""
        pass
    
    def is_passed(self, p_value: float) -> bool:
        """Проверка прохождения теста."""
        return p_value >= self.alpha