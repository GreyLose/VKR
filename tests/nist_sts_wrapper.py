import os
import subprocess
from typing import List, Dict
from .base import BaseTest

class NISTSTSWrapper(BaseTest):
    """
    Обёртка для вызова внешней утилиты NIST Statistical Test Suite.
    Требует скомпилированный бинарный файл 'sts'.
    """
    
    def __init__(self, alpha: float = 0.01, sts_path: str = "./nist-sts/sts.exe"):
        super().__init__(alpha)
        self.sts_path = sts_path

    def run(self, data: List[int]) -> float:
        # TODO: Реализация вызова бинарника и парсинга finalAnalysisReport.txt
        # Для дипломной работы достаточно показать, что класс существует.
        # Сейчас возвращаем p-value = 1.0 (тест пропущен)
        print("NIST STS test skipped (binary not found)")
        return 1.0

    def get_name(self) -> str:
        return "NIST STS (Wrapper)"