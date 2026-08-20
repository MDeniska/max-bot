"""
Обработчики текстовых сообщений и фото
"""
import logging
from flask import jsonify

import database as db
from app.utils import max_api
# Временно отключаем клавиатуры для чистого теста
# from app import keyboards 
from app import messages

logger = logging.getLogger("bot")


def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        
        message_id = message.get('id') or message.get('message_id') or data.get('update_id')
        if message_id:
            if db.is_message_processed(message_id):
                logger.info(f"🔁 Дубликат сообщения {message_id} — пропускаем")
                return jsonify({"ok": True}), 200
            db.mark_message_processed(message_id)
        
        text = message.get('body', {}).get('text', '').strip()
        
        if not text:
            return jsonify({"ok": True}), 200
        
        logger.info(f"📩 Текст: '{text}' | user_id={user_id} | chat_id={chat_id}")
        
        if user_id and chat_id:
            db.save_chat_id(user_id, chat_id)
        
        if text.lower() == "/start":
            db.set_user_state(user_id, 'idle')
            
            # ТЕСТ: отправляем ТОЛЬКО текст, БЕЗ attachments (клавиатуры)
            test_text = f"👋 Привет, {first_name}! Бот работает и видит тебя. Это тестовое сообщение без кнопок."
            max_api.send_message(chat_id, test_text)
            
            return jsonify({"ok": True}), 200
        
        max_api.send_message(chat_id, "Я пока учусь! Напиши /start")
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ Исключение в handle_message: {e}", exc_info=True)
        return jsonify({"ok": True}), 200
