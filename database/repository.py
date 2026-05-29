"""
database/repository.py
Репозитории для работы с базой данных (паттерн Repository)
"""

from sqlalchemy.orm import Session, selectinload
from typing import List, Optional, Tuple, Any
from sqlalchemy import func, case, Integer
from .models import Generator, TestResult


class GeneratorRepository:
    """Репозиторий для работы с таблицей генераторов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, gen_type: str, params: dict, 
               description: Optional[str] = None) -> Generator:
        """Создать новую запись эксперимента"""
        gen = Generator(
            name=name,
            gen_type=gen_type,
            parameters=params,
            description=description
        )
        self.db.add(gen)
        self.db.commit()
        self.db.refresh(gen)
        return gen
    
    def get_history(self, limit: int = 100) -> List[Generator]:
        """Получить последние N экспериментов с подгрузкой результатов"""
        return (self.db.query(Generator)
                .options(selectinload(Generator.test_results))
                .order_by(Generator.created_at.desc())
                .limit(limit)
                .all())
    
    def get_aggregated_statistics(self) -> List[Tuple[Any, ...]]:
        """
        Агрегированная статистика по генераторам.
        Возвращает: (gen_type, total_experiments, total_tests, passed_count, avg_p_value)
        """
        # Используем CASE для надёжного подсчёта boolean в PostgreSQL
        return (self.db.query(
                Generator.gen_type,
                func.count(Generator.id.distinct()).label('total_experiments'),
                func.count(TestResult.id).label('total_tests'),
                # Надёжный подсчёт: True → 1, False → 0
                func.sum(case((TestResult.passed.is_(True), 1), else_=0)).label('passed_tests'),
                func.avg(TestResult.p_value).label('avg_p_value')
            )
            .join(TestResult, Generator.id == TestResult.generator_id)
            .group_by(Generator.gen_type)
            .all())
    
    def get_test_statistics_by_generator(self) -> List[Tuple[Any, ...]]:
        """Статистика по каждому тесту для каждого генератора"""
        return (self.db.query(
                Generator.gen_type,
                TestResult.test_name,
                func.count(TestResult.id).label('total'),
                func.sum(case((TestResult.passed.is_(True), 1), else_=0)).label('passed'),
                func.avg(TestResult.p_value).label('avg_p_value')
            )
            .join(Generator, Generator.id == TestResult.generator_id)
            .group_by(Generator.gen_type, TestResult.test_name)
            .order_by(Generator.gen_type, TestResult.test_name)
            .all())
    
    def get_overall_summary(self) -> Optional[Tuple[int, int, float]]:
        """Общая сводка по всей базе"""
        return (self.db.query(
                func.count(Generator.id.distinct()).label('total_experiments'),
                func.count(TestResult.id).label('total_tests'),
                func.avg(TestResult.p_value).label('avg_p_value')
            )
            .join(TestResult, Generator.id == TestResult.generator_id)
            .first())


class TestResultRepository:
    """Репозиторий для работы с таблицей результатов тестов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def bulk_create(self, results: List[dict]) -> List[TestResult]:
        """Массовое создание записей результатов тестов"""
        db_results = [TestResult(**r) for r in results]
        self.db.add_all(db_results)
        self.db.commit()
        for r in db_results:
            self.db.refresh(r)
        return db_results
    
    def get_by_generator(self, gen_id: int) -> List[TestResult]:
        """Получить все результаты тестов для конкретного эксперимента"""
        return (self.db.query(TestResult)
                .filter(TestResult.generator_id == gen_id)
                .all())