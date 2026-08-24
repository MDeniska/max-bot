"""
Генератор мемов через memegen.link (быстро, бесплатно, без очередей)
"""
import requests
import logging
import random
import urllib.parse
import os

logger = logging.getLogger("bot")

# Список популярных и безопасных шаблонов (ID из memegen.link)
POPULAR_TEMPLATES = [
    "drake",             # Drake Hotline Bling
    "distracted",        # Distracted Boyfriend
    "change_my_mind",    # Change My Mind
    "is_this",           # Is this a pigeon?
    "two_buttons",       # Two Buttons
    "left_exit_12",      # Left Exit 12
    "success_kid",       # Success Kid
    "roll_safe",         # Roll Safe
    "one_does_not_simply", # One Does Not Simply
    "ancient_aliens"     # Ancient Aliens
]

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def generate_meme(text: str) -> bytes:
    """Генерирует мем и возвращает его байты"""
    
    # 1. Разделяем текст на верхний и нижний (по разделителю |)
    if "|" in text:
        parts = text.split("|", 1)
        text0 = parts[0].strip()
        text1 = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Если разделителя нет, весь текст идет вниз, а сверху классическое "Когда..."
        text0 = "Когда"
        text1 = text.strip()
    
    # 2. Выбираем случайный шаблон
    template_id = random.choice(POPULAR_TEMPLATES)
    logger.info(f"🎭 Генерация мема: шаблон='{template_id}', верх='{text0}', низ='{text1}'")
    
    # 3. Кодируем текст для URL (поддержка русского языка)
    encoded_text0 = urllib.parse.quote(text0, safe='')
    encoded_text1 = urllib.parse.quote(text1, safe='')
    
    # 4. Формируем URL (memegen.link сам рендерит картинку по URL)
    # Если нижнего текста нет, URL выглядит как /images/template/text0.jpg
    if encoded_text1:
        url = f"https://api.memegen.link/images/{template_id}/{encoded_text0}/{encoded_text1}.jpg"
    else:
        url = f"https://api.memegen.link/images/{template_id}/{encoded_text0}.jpg"
    
    logger.info(f"🔗 URL мема: {url}")
    
    # 5. Скачиваем готовую картинку
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Мем успешно скачан ({len(response.content)} байт)")
        return response.content
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания мема: {e}")
        raise Exception("Не удалось создать мем. Попробуй другой текст.")


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
        files = {"data": ("meme.jpg", image_bytes, "image/jpeg")}
        file_response = requests.post(upload_url, files=files, timeout=30)
        
        if file_response.status_code != 200:
            logger.error(f"❌ MAX API: ошибка загрузки файла: {file_response.text}")
            return None
        
        file_data = file_response.json()
        photos = file_data.get("photos", {})
        if photos:
            first_photo_key = next(iter(photos.keys()))
            token = photos[first_photo_key].get("token")
            logger.info(f"✅ Мем загружен на MAX API, token: {token[:20]}...")
            return token
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки на MAX API: {e}")
        return None
