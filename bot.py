import os
from flask import Flask, jsonify, request

print("=" * 60)
print("!!! ЗАПУСК BOT.PY НА BOTHOST !!!")
print(f"PORT из окружения: {os.getenv('PORT', 'НЕ НАЙДЕН')}")
print(f"MAX_BOT_TOKEN: {'НАЙДЕН' if os.getenv('MAX_BOT_TOKEN') else 'НЕ НАЙДЕН'}")
print("=" * 60)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "test"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    print("Получен запрос на /webhook!")
    return jsonify({"ok": True}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 3000))
    print(f"!!! СЕРВЕР ЗАПУЩЕН НА host=0.0.0.0, port={port} !!!")
    app.run(host="0.0.0.0", port=port, debug=False)
