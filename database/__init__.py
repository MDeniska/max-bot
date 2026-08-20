from database.connection import SessionLocal, Base, init_db
from database.users import User

# Заглушки для остальных таблиц, чтобы импорты в bot.py не падали
class Recipe: pass
class Ingredient: pass
class GeneratedImage: pass
class WebhookLog: pass
class Reminder: pass

__all__ = [
    "init_db", "save_chat_id", "set_user_state", "get_user_state", 
    "save_temp_data", "get_temp_data", "is_message_processed", "mark_message_processed"
]

# --- Функции для работы с БД, которые вызывает бот ---

def save_chat_id(user_id: str, chat_id: str):
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == str(user_id)).first()
        if not user:
            user = User(user_id=str(user_id), chat_id=str(chat_id))
            db.add(user)
        else:
            user.chat_id = str(chat_id)
        db.commit()

def set_user_state(user_id: str, state: str):
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == str(user_id)).first()
        if user:
            user.state = state
            db.commit()

def get_user_state(user_id: str) -> str:
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == str(user_id)).first()
        return user.state if user else "idle"

def save_temp_data(user_id: str, data: str):
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == str(user_id)).first()
        if user:
            user.temp_data = str(data)
            db.commit()

def get_temp_data(user_id: str) -> str:
    with SessionLocal() as db:
        user = db.query(User).filter(User.user_id == str(user_id)).first()
        return user.temp_data if user else ""

# --- Временная защита от дублей (в оперативной памяти) ---
_processed_messages = set()

def is_message_processed(message_id: str) -> bool:
    return str(message_id) in _processed_messages

def mark_message_processed(message_id: str):
    _processed_messages.add(str(message_id))
