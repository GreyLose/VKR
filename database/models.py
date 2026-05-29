from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Generator(Base):
    """Модель генератора (хранит параметры и тип ГСЧ)"""
    __tablename__ = "generators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)      # Название (lcg, mersenne, xorshift, truerng)
    gen_type = Column(String(50))                   # Тип генератора
    parameters = Column(JSON)                       # Параметры (a, m, c, seed и т.д.)
    description = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    
    # Связь 1 ко многим: один генератор → много результатов тестов
    test_results = relationship("TestResult", back_populates="generator", cascade="all, delete-orphan")

class TestResult(Base):
    """Модель результата статистического теста"""
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    generator_id = Column(Integer, ForeignKey("generators.id", ondelete="CASCADE"), nullable=False)
    
    test_name = Column(String(100), nullable=False) # Monobit, Runs, Autocorrelation, ChiSquare
    p_value = Column(Float, nullable=False)
    statistic = Column(Float)
    passed = Column(Boolean, default=False)         # p_value >= alpha
    
    sequence_length = Column(Integer)
    test_parameters = Column(JSON)                  # lag, bins и др.
    execution_time = Column(Float)                  # Время выполнения теста (мс)
    created_at = Column(DateTime, server_default=func.now())
    
    generator = relationship("Generator", back_populates="test_results")