from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Настройки подключения к PostgreSQL"""
    host: str = "localhost"
    port: int = 5432
    database: str = "rng_quality_db"
    user: str = "postgres"
    password: str = "1111"
    echo_sql: bool = False

    @property
    def url(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class AppConfig:
    """Общие параметры системы"""
    title: str = "Исследование качества ГСЧ/ГПСЧ"
    version: str = "1.0.0"
    default_seed: int = 12345
    max_sequence_length: int = 1_000_000

# Глобальные экземпляры для импорта в других модулях
db_config = DatabaseConfig()
app_config = AppConfig()