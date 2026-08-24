"""
Официальный клиент для генерации изображений через GigaChat API (Sber)
Нативная поддержка русского языка, 100% работает на российских серверах (nsk7).
"""
import os
import logging
import requests
import base64
import re
import uuid

logger = logging.getLogger("bot")

AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY", "").strip()
CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET", "").strip()

if AUTH_KEY:
    BASIC_AUTH = AUTH_KEY if AUTH_KEY.startswith("Basic ") else f"Basic {AUTH_KEY}"
else:
    encoded_credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode('utf-8')).decode('utf-8')
    BASIC_AUTH = f"Basic {encoded_credentials}"

AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
FILE_URL = "https://gigachat.devices.sberbank.ru/api/v1/files/{}/content"

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def get_gigachat_token() -> str:
    """Получает токен доступа для GigaChat API"""
    auth_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": BASIC_AUTH
    }
    
    try:
        response = requests.post(AUTH_URL, headers=auth_headers, data="scope=GIGACHAT_API_PERS", timeout=10, verify=CERT_PATH)
        response.raise_for_status()
        token = response.json().get("access_token")
        logger.info("✅ Токен GigaChat успешно получен")
        return token
    except requests.exceptions.RequestException:
        logger.warning("⚠️ Ошибка сертификата, пробуем без проверки...")
        response = requests.post(AUTH_URL, headers=auth_headers, data="scope=GIGACHAT_API_PERS", timeout=10, verify=False)
        response.raise_for_status()
        logger.info("✅ Токен GigaChat успешно получен (без проверки сертификата)")
        return response.json().get("access_token")


def generate_image(prompt: str) -> bytes:
    """Генерирует картинку по русскоязычному промпту через GigaChat API"""
    logger.info(f"🎨 GigaChat (Kandinsky): генерация по запросу '{prompt[:50]}...'")
    
    token = get_gigachat_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": "GigaChat-Pro",
        "messages": [
            {"role": "system", "content": "Ты — профессиональный художник, создающий изображения по описанию."},
            {"role": "user", "content": f"Нарисуй: {prompt}"}
        ],
        "function_call": "auto"
    }
    
    try:
        # 1. Запрашиваем генерацию
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60, verify=False)
        
        if response.status_code == 429:
            raise Exception("Слишком много запросов. Подождите 60 секунд и попробуйте снова.")
            
        response.raise_for_status()
        data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        logger.info("📝 Ответ модели получен")
        
        # 2. Извлекаем file_id
        match = re.search(r'<img\s+src="([a-f0-9\-]+)"', content, re.IGNORECASE)
        if not match:
            raise Exception(f"Модель не вернула изображение. Ответ: {content}")
            
        file_id = match.group(1)
        logger.info(f"✅ Получен file_id изображения: {file_id}")
        
        # 3. Скачиваем изображение
        file_headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json, image/jpeg, image/png"
        }
        
        file_response = requests.get(FILE_URL.format(file_id), headers=file_headers, timeout=30, verify=False)
        file_response.raise_for_status()
        
        # 4. УМНАЯ ОБРАБОТКА: проверяем, что вернул сервер (raw картинку или JSON с base64)
        content_type = file_response.headers.get('Content-Type', '')
        
        if 'image' in content_type:
            # Сервер вернул саму картинку байтами
            image_bytes = file_response.content
            logger.info(f"✅ Картинка успешно получена (raw bytes, {len(image_bytes)} байт)")
        else:
            # Сервер вернул JSON с base64 строкой
            file_data = file_response.json()
            image_b64 = file_data.get("content", "")
            if not image_b64:
                raise Exception(f"Пустое поле content в ответе: {file_data}")
            image_bytes = base64.b64decode(image_b64)
            logger.info(f"✅ Картинка успешно получена (base64, {len(image_bytes)} байт)")
            
        return image_bytes
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise Exception("Слишком много запросов. Подождите 60 секунд и попробуйте снова.")
        raise Exception(f"Ошибка HTTP: {e}")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА GIGACHAT: {str(e)}")
        raise Exception(f"Сбой генерации: {str(e)}")


def upload_to_max_api(image_bytes):
    """Загружает байты картинки на MAX API и возвращает token"""
    try:
        upload_response = requests.post(
            f"https://platform-api2.max.ru/uploads?type=image",
            headers={"Authorization": BOT_TOKEN, "Content-Type": "application/json"},
            timeout=10,
            verify=CERT_PATH
        )
        if upload_response.status_code != 200:
            logger.error(f"❌ MAX API: ошибка получения URL: {upload_response.text}")
            return None
        
        upload_url = upload_response.json().get("url")
        files = {"data": ("gigachat.jpg", image_bytes, "image/jpeg")}
        file_response = requests.post(upload_url, files=files, timeout=30)
        
        if file_response.status_code != 200:
            logger.error(f"❌ MAX API: ошибка загрузки файла: {file_response.text}")
            return None
        
        file_data = file_response.json()
        photos = file_data.get("photos", {})
        if photos:
            first_photo_key = next(iter(photos.keys()))
            token = photos[first_photo_key].get("token")
            logger.info(f"✅ Картинка загружена на MAX API, token: {token[:20]}...")
            return token
            
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки на MAX API: {e}")
        return None
