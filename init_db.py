
from database import Base, engine
from sqlalchemy import inspect

def init():
    # Проверяем, существует ли таблица
    inspector = inspect(engine)
    if inspector.has_table('test_results'):
        print("Таблица test_results уже существует. Удаляем...")
        from sqlalchemy import MetaData, Table
        metadata = MetaData()
        test_results = Table('test_results', metadata)
        test_results.drop(engine)
        print("Таблица удалена")
    
    # Создаём таблицы заново
    Base.metadata.create_all(bind=engine)
    print("База данных успешно инициализирована!")

if __name__ == "__main__":
    init()