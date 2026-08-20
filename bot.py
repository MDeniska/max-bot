import os
import json
import requests
from flask import Flask, jsonify, request

print("=" * 60)
print("!!! ЗАПУСК BOT.PY НА BOTHOST !!!")
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-1786971397-7403-mdenis.bothost.tech/webhook")
print(f"PORT: {os.getenv('PORT', '3000')}")
print(f"MAX_BOT_TOKEN: {'НАЙДЕН' if BOT_TOKEN else 'НЕ НАЙДЕН'}")
print("=" * 60)

app = Flask(__name__)
MAX_API_URL = "https://platform-api2.max.ru"

# 1. Функция отправки сообщения в MAX
def send_message(chat_id, text):
    url = f"{MAX_API_URL}/messages"
    headers = {
        "Authorization": BOT_TOKEN,
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {"text": text}
    try:
        response = requests.post(url, params={"chat_id": chat_id}, json=payload, headers=headers, timeout=10)
        print(f"📤 Отправка в {chat_id}: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# 2. Функция регистрации вебхука (вызывается при старте)
def register_webhook():
    url = f"{MAX_API_URL}/subscriptions"
    headers = {
        "Authorization": BOT_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "url": WEBHOOK_URL,
        "update_types": ["message_created", "message_callback"]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"✅ Регистрация вебхука: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Ошибка регистрации вебхука: {e}")

# 3. Главный обработчик сообщений
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"ok": True}), 200

        update_type = data.get('update_type')

        # Если пришло новое сообщение
        if update_type == 'message_created':
            message = data.get('message', {})
            chat_id = message.get('recipient', {}).get('chat_id')
            user_info = message.get('sender', {})
            first_name = user_info.get('first_name', 'Пользователь')
            text = message.get('body', {}).get('text', '').strip()

            print(f"📩 Получено сообщение от {first_name}: '{text}'")

            # Реакция на команду /start
            if text.lower() == '/start':
                welcome_text = f"👋 Привет, {first_name}!\n\n🎉 Бот успешно запущен и готов к работе!\n\nСкоро здесь появится меню с AI-аватарками, генерацией картинок и другими развлечениями."
                send_message(chat_id, welcome_text)

        # Если нажали на кнопку (пока просто логируем)
        elif update_type == 'message_callback':
            print("🔘 Получен callback (нажатие кнопки)")

        return jsonify({"ok": True}), 200
    
    except Exception as e:
        print(f"❌ Критическая ошибка в webhook: {e}")
        return jsonify({"ok": True}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "test"}), 200

if __name__ == '__main__':
    # Регистрируем вебхук ПЕРЕД запуском сервера
    register_webhook()
    
    port = int(os.getenv("PORT", 3000))
    print(f"!!! СЕРВЕР ЗАПУЩЕН НА host=0.0.0.0, port={port} !!!")
    app.run(host="0.0.0.0", port=port, debug=False)
