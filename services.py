from database import get_session, UserRepository, GeneratorRepository, TestResultRepository
from datetime import datetime

class DBService:
    """Сервис для работы с базой данных"""
    
    def __init__(self):
        self.db = next(get_session())
        self.users = UserRepository(self.db)
        self.gens = GeneratorRepository(self.db)
        self.results = TestResultRepository(self.db)
        
        # Дефолтный пользователь для учебных экспериментов
        self.user = self.users.get_by_username("student")
        if not self.user:
            self.user = self.users.create(username="student")

    def save_experiment(self, gen_type: str, seed: int, length: int, 
                       gen_params: dict, test_results: list):
        """
        Сохранение результатов эксперимента в БД
        
        :param gen_type: тип генератора (lcg, mersenne, xorshift)
        :param seed: зерно генератора
        :param length: длина последовательности
        :param gen_params: параметры генератора
        :param test_results: список результатов тестов
        """
        # Создаем запись о генераторе
        gen = self.gens.create(
            user_id=self.user.id,
            name=f"{gen_type.upper()}_seed{seed}",
            gen_type=gen_type,
            params=gen_params
        )
        
        # Формируем записи результатов тестов
        records = [
            {
                "user_id": self.user.id,
                "generator_id": gen.id,
                "test_name": r["name"],
                "p_value": r["p_value"],
                "statistic": r.get("statistic"),
                "passed": r["passed"],
                "sequence_length": length,
                "test_parameters": {"alpha": r.get("alpha", 0.01)},
                "execution_time": r.get("execution_time")
            }
            for r in test_results
        ]
        
        # Сохраняем результаты
        self.results.bulk_create(records)
        return gen.id

    def get_last_experiments(self, limit: int = 5):
        """
        Получение последних экспериментов
        
        :param limit: количество записей
        :return: список экспериментов
        """
        query = """
        SELECT g.name, g.gen_type, t.test_name, t.p_value, t.passed, t.created_at
        FROM test_results t
        JOIN generators g ON t.generator_id = g.id
        ORDER BY t.created_at DESC LIMIT %s
        """
        cursor = self.db.connection().cursor()
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    
    def close(self):
        """Закрытие соединения с БД"""
        self.db.close()