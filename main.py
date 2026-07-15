import os
import json
from flask import Flask, request, jsonify
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

app = Flask(__name__)

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "f9LHodD0cOINzzDcw0J-TWsM8ZGee43BRWdy8czR8Gfhj8k7HHYVs9TbmMp07hGZa2jw2Vyq35mUNCHvKiJh")
MAX_API = "https://platform-api.max.ru"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info("Пришло сообщение от MAX: %s", data)
    
    if data and 'message' in data:
        chat_id = data['message']['recipient']['chat_id']
        text = data['message'].get('body', {}).get('text', '').lower()
        
        # Логика бота
        if text in ['hello', 'hi', 'привет', 'здравствуй']:
            reply = "Привет! Я бот на MaxBot. Как дела?"
        elif text in ['good bye', 'bye', 'пока', 'до свидания']:
            reply = "До свидания! Удачи!"
        elif text == '/start':
            reply = "Добро пожаловать! Я бот на MaxBot. Напишите 'привет' или 'hello' для начала."
        else:
            reply = "Извините, я не понял. Попробуйте написать 'привет' или '/start'."
        
        # Отправляем ответ через API MAX
        try:
            response = requests.post(
                f"{MAX_API}/messages",
                params={"chat_id": chat_id},
                json={"text": reply},
                headers={"Authorization": BOT_TOKEN, "Content-Type": "application/json"},
                timeout=30
            )
            logger.info("Ответ отправлен, статус: %s", response.status_code)
        except Exception as e:
            logger.error("Ошибка при отправке: %s", e)
    
    return jsonify({"ok": True})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
