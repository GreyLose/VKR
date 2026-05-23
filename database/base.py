from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import db_config, ENGINE_KWARGS

# Создание движка с указанием кодировки
engine = create_engine(
    db_config.url,
    **ENGINE_KWARGS
)

# Фабрика сессий (связь с БД)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Базовый класс для всех моделей
Base = declarative_base()

def get_session():
    """Генератор для получения сессии (используется в приложениях)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()