"""
Функции для работы с MAX API (отправка сообщений)
"""
import os
import json
import logging
import requests

logger = logging.getLogger("bot")

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
MAX_API = "https://platform-api2.max.ru"
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def send_message(chat_id, text, attachments=None):
    """Отправляет текстовое сообщение или сообщение с кнопками"""
    headers = {"Authorization": BOT_TOKEN, "Content-Type": "application/json; charset=utf-8"}
    payload = {"text": text}
    if attachments:
        payload["attachments"] = attachments
    
    data_str = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    
    try:
        response = requests.post(
            f"{MAX_API}/messages",
            params={"chat_id": chat_id},
            data=data_str,
            headers=headers,
            timeout=10,
            verify=CERT_PATH
        )
        if response.status_code != 200:
            logger.error(f"❌ MAX API ответил: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False


def send_image_message(chat_id, text, image_token):
    """Отправляет сообщение с картинкой"""
    attachments = [{"type": "image", "payload": {"token": image_token}}]
    return send_message(chat_id, text, attachments=attachments)


def answer_callback(callback_id, text):
    """Отвечает на callback (нажатие кнопки)"""
    headers = {"Authorization": BOT_TOKEN, "Content-Type": "application/json; charset=utf-8"}
    data_str = json.dumps({"message": {"text": text}}, ensure_ascii=False).encode('utf-8')
    try:
        response = requests.post(
            f"{MAX_API}/answers",
            params={"callback_id": callback_id},
            data=data_str,
            headers=headers,
            timeout=10,
            verify=CERT_PATH
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Ошибка callback: {e}")
        return False


def register_webhook(webhook_url):
    """Регистрирует webhook в MAX API"""
    payload = {"url": webhook_url, "update_types": ["message_created", "message_callback"]}
    try:
        response = requests.post(
            f"{MAX_API}/subscriptions",
            json=payload,
            headers={"Authorization": BOT_TOKEN, "Content-Type": "application/json"},
            timeout=10,
            verify=CERT_PATH
        )
        logger.info(f"✅ Вебхук зарегистрирован: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации вебхука: {e}")
        return False
