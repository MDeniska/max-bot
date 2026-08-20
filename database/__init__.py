import logging

logger = logging.getLogger("database")

# Простая инициализация (заглушка, чтобы не падал импорт)
def init_db():
    logger.info("🗄️ База данных инициализирована (заглушка)")

def save_chat_id(user_id, chat_id):
    pass

def set_user_state(user_id, state):
    pass

def get_user_state(user_id):
    return "idle"

def save_temp_data(user_id, data):
    pass

def get_temp_data(user_id):
    return ""

# Защита от дублей в памяти
_processed_messages = set()

def is_message_processed(message_id):
    return str(message_id) in _processed_messages

def mark_message_processed(message_id):
    _processed_messages.add(str(message_id))
