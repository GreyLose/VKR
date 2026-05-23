from config import db_config

# Параметры для инициализации SQLAlchemy Engine
ENGINE_KWARGS = {
    "echo": db_config.echo_sql,
    "pool_pre_ping": True,  # Проверяет соединение перед использованием
    "connect_args": {"client_encoding": "utf8"}
}

__all__ = ["db_config", "ENGINE_KWARGS"]