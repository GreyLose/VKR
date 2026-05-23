from sqlalchemy.orm import Session
from typing import List, Optional
from .models import User, Generator, TestResult

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, username: str) -> User:
        user = User(username=username)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

class GeneratorRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_id: int, name: str, gen_type: str, params: dict) -> Generator:
        gen = Generator(user_id=user_id, name=name, gen_type=gen_type, parameters=params)
        self.db.add(gen)
        self.db.commit()
        self.db.refresh(gen)
        return gen

class TestResultRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def bulk_create(self, results: List[dict]) -> List[TestResult]:
        """Массовое создание записей результатов"""
        db_results = [TestResult(**r) for r in results]
        self.db.add_all(db_results)
        self.db.commit()
        for r in db_results:
            self.db.refresh(r)
        return db_results
    
    def get_by_generator(self, gen_id: int) -> List[TestResult]:
        return self.db.query(TestResult).filter(TestResult.generator_id == gen_id).all()