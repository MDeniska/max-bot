import logging
from flask import jsonify
from app.utils import max_api
from app import keyboards
from app import messages

logger = logging.getLogger("bot")

def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        text = message.get('body', {}).get('text', '').strip()
        
        logger.info(f"📩 Текст: '{text}' | user_id={user_id}")
        
        if text.lower() == "/start":
            max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_menu_keyboard())
            return jsonify({"ok": True}), 200
            
        # Временный ответ на любой другой текст
        max_api.send_message(chat_id, "Я пока учусь! Нажми /start, чтобы увидеть меню.", attachments=keyboards.get_back_keyboard())
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"❌ Исключение в handle_message: {e}", exc_info=True)
        return jsonify({"ok": True}), 200
