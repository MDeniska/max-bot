import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("database")

# Используем абсолютный путь к папке /app/data для Bothost (там есть права на запись)
# Если папки нет, используем обычную локальную базу
default_db = "sqlite:////app/data/bot.db" if os.path.exists("/app/data") else "sqlite:///bot.db"
DATABASE_URL = os.getenv("DATABASE_URL", default_db)

logger.info(f"🔗 Подключение к БД по пути: {DATABASE_URL}")

# Создаем движок базы данных
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

def init_db():
    """Создает все таблицы, если их еще нет"""
    logger.info("🗄️ Инициализация базы данных (создание таблиц)...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы успешно созданы или уже существуют!")
