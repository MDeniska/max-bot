"""
Главный файл бота — тонкий роутер между Flask и обработчиками
"""
import os
import json
import logging
from flask import Flask, request, jsonify

# Эти принты гарантируют, что мы увидим старт в логах Bothost даже при ошибке импорта
print("=" * 60)
print("!!! ЗАПУСК BOT.PY НА BOTHOST !!!")
print(f"PORT: {os.getenv('PORT', '3000')}")
print(f"MAX_BOT_TOKEN: {'НАЙДЕН' if os.getenv('MAX_BOT_TOKEN') else 'НЕ НАЙДЕН'}")
print("=" * 60)

import database as db
from app.utils import max_api
from app.handlers import callbacks, messages as msg_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Инициализация БД
db.init_db()
logger.info("!!! КОНТРОЛЬНАЯ ТОЧКА: bot.py MODULAR + ERROR-HANDLING !!!")

# ВАЖНО: Используем URL твоего НОВОГО бота
WEBHOOK_URL = "https://bot-1786971397-7403-mdenis.bothost.tech/webhook"
max_api.register_webhook(WEBHOOK_URL)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Главный endpoint — роутит обновления к обработчикам"""
    try:
        raw_data = request.get_data(as_text=True)
        try:
            data = json.loads(raw_data)
        except:
            data = request.json
        
        if not data:
            return jsonify({"ok": True}), 200

        update_type = data.get('update_type')

        # --- Нажатие кнопки ---
        if update_type == 'message_callback':
            callback = data.get('callback', {})
            callback_id = callback.get('callback_id')
            payload_data = callback.get('payload', '')
            user_info = callback.get('user', {})
            user_id = user_info.get('user_id')
            first_name = user_info.get('first_name', 'Пользователь')
            chat_id = data.get('message', {}).get('recipient', {}).get('chat_id')
            
            result = callbacks.handle_callback(payload_data, chat_id, user_id, first_name, callback_id)
            return result if result else (jsonify({"ok": True}), 200)

        # --- Текстовое сообщение или фото ---
        if update_type == 'message_created':
            message = data.get('message', {})
            chat_id = message.get('recipient', {}).get('chat_id')
            user_info = message.get('sender', {})
            user_id = user_info.get('user_id')
            first_name = user_info.get('first_name', 'Пользователь')
            
            result = msg_handlers.handle_message(data, chat_id, user_id, first_name)
            return result if result else (jsonify({"ok": True}), 200)
        
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в webhook: {e}", exc_info=True)
        return jsonify({"ok": True}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 3000))
    logger.info(f"🚀 Бот запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
