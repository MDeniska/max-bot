import os
from flask import Flask, request, jsonify
import requests
import urllib3
import hmac
import logging

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

app = Flask(__name__)

# Токен из переменной окружения
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "f9LHodD0cOINzzDcw0J-TWsM8ZGee43BRWdy8czR8Gfhj8k7HHYVs9TbmMp07hGZa2jw2Vyq35mUNCHvKiJh")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
MAX_API = "https://platform-api.max.ru"

def auth_value():
    return BOT_TOKEN

def api_headers():
    return {
        "Authorization": auth_value(),
        "Content-Type": "application/json",
    }

@app.route('/webhook', methods=['POST', 'HEAD'])
def webhook():
    if request.method == "HEAD":
        return "", 200

    # Проверка секрета (если задан)
    if WEBHOOK_SECRET:
        got = request.headers.get("X-Max-Bot-Api-Secret", "")
        if not hmac.compare_digest(got, WEBHOOK_SECRET):
            return jsonify({"error": "forbidden"}), 403

    data = request.json
    logger.info("Пришло сообщение от MAX: %s", data)
    
    # Проверяем, есть ли сообщение
    if data and 'message' in data:
        # Извлекаем данные
        chat_id = data['message']['recipient']['chat_id']
        text = data['message'].get('body', {}).get('text', '')
        
        # Формируем ответ
        if text == '/start':
            reply = "🚀 Привет! Я Бизнес-Ассистент 24/7!"
        else:
            reply = f"📩 Вы написали: {text}"
        
        # Отправляем ответ через правильный API MAX
        try:
            response = requests.post(
                f"{MAX_API}/messages",
                params={"chat_id": chat_id},
                json={"text": reply},
                headers=api_headers(),
                verify=False,
                timeout=30
            )
            logger.info("Ответ отправлен, статус: %s", response.status_code)
        except Exception as e:
            logger.error("Ошибка при отправке: %s", e)
    
    return jsonify({"ok": True})

@app.route('/')
def index():
    return "Бот работает на Bothost.ru!"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
