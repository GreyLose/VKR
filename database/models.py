from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    """Модель пользователя (Таблица 'Пользователь' из отчета)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Связь 1 ко многим
    generators = relationship("Generator", back_populates="user", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="user")

class Generator(Base):
    """Модель генератора (Таблица 'ГПСЧ' из отчета)"""
    __tablename__ = "generators"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(100), nullable=False) # Название ГПСЧ
    gen_type = Column(String(50))              # Тип (lcg, mersenne...)
    parameters = Column(JSON)                  # Параметры (a, m, c, seed)
    description = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="generators")
    test_results = relationship("TestResult", back_populates="generator", cascade="all, delete-orphan")

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    generator_id = Column(Integer, ForeignKey("generators.id", ondelete="CASCADE"))
    
    test_name = Column(String(100), nullable=False)
    p_value = Column(Float, nullable=False)
    statistic = Column(Float)
    passed = Column(Boolean, default=False)
    
    sequence_length = Column(Integer)
    test_parameters = Column(JSON)
    execution_time = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="test_results")
    generator = relationship("Generator", back_populates="test_results")