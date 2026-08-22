"""
Функции для работы с MAX API (отправка сообщений)
"""
import os
import json
import logging
import requests

logger = logging.getLogger("bot")

# Берем токен из настроек Bothost (безопасно!)
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
MAX_API = "https://platform-api2.max.ru"

# Железобетонный путь к сертификату (как в рабочем боте)
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
        
        # ЖЕСТКИЙ ВЫВОД ОШИБКИ В ЛОГИ
        if response.status_code != 200:
            print(f"!!! КРИТИЧЕСКАЯ ОШИБКА MAX API {response.status_code}: {response.text} !!!")
            logger.error(f"❌ MAX API ответил: {response.text}")
        else:
            logger.info(f"📤 Отправка на chat_id={chat_id}. Код: {response.status_code}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"!!! ИСКЛЮЧЕНИЕ ПРИ ОТПРАВКЕ: {e} !!!")
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

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
        logger.info(f"✅ Callback ответ: {response.status_code}")
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
def download_image_from_max(image_token: str) -> bytes:
    """Скачивает изображение из MAX API по токену"""
    # URL для скачивания файлов в MAX API
    file_url = f"{MAX_API}/files/{image_token}"
    try:
        response = requests.get(
            file_url,
            headers={"Authorization": BOT_TOKEN},
            timeout=15,
            verify=CERT_PATH
        )
        response.raise_for_status()
        logger.info(f"✅ Картинка {image_token} успешно скачана")
        return response.content
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания картинки {image_token}: {e}")
        return None


def upload_image_to_max(image_bytes: bytes, filename: str = "avatar.jpg") -> str:
    """Загружает изображение в MAX API и возвращает новый токен"""
    upload_url = f"{MAX_API}/files"
    try:
        files = {'file': (filename, image_bytes, 'image/jpeg')}
        response = requests.post(
            upload_url,
            headers={"Authorization": BOT_TOKEN},
            files=files,
            timeout=15,
            verify=CERT_PATH
        )
        response.raise_for_status()
        # MAX API возвращает JSON с токеном загруженного файла
        new_token = response.json().get("token")
        logger.info(f"✅ Картинка успешно загружена, новый токен: {new_token}")
        return new_token
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки картинки в MAX: {e}")
        return None
