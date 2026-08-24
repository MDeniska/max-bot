"""
Генератор мемов через memegen.link (Идеальный шрифт Impact)
Использует формат пути URL, который является официальным и самым стабильным.
"""
import requests
import logging
import random
import os

logger = logging.getLogger("bot")

# Только самые надежные шаблоны, которые отлично смотрятся с 1-2 строками текста
TEMPLATES = [
    "drake",             # Drake Hotline Bling
    "two_buttons",       # Two Buttons (Daily Struggle)
    "is_this",           # Is this a pigeon?
    "success",           # Success Kid
    "always_has_been",   # Always Has Been (Astronaut)
    "left_exit_12"       # Left Exit 12 Off Ramp
]

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def clean_text(text: str) -> str:
    """Заменяет пробелы на подчеркивания. requests сам корректно закодирует кириллицу."""
    return text.strip().replace(" ", "_")


def generate_meme(text: str) -> bytes:
    """Генерирует мем через memegen.link"""
    
    # 1. Умное разделение текста по слэшу или тире
    separators = ['/', '-', '—', '|']
    split_char = None
    for sep in separators:
        if sep in text:
            split_char = sep
            break
            
    if split_char:
        parts = text.split(split_char, 1)
        text_top = parts[0].strip()
        text_bottom = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Если разделителя нет, текст идет вниз, а сверху будет пусто (_)
        text_top = ""
        text_bottom = text.strip()

    logger.info(f"🎭 Генерация мема: верх='{text_top}', низ='{text_bottom}'")

    # 2. Выбираем случайный шаблон
    template_id = random.choice(TEMPLATES)
    
    # 3. Формируем URL в формате пути. 
    # requests автоматически и корректно закодирует кириллицу (ровно один раз!)
    if text_top and text_bottom:
        url = f"https://api.memegen.link/images/{template_id}/{clean_text(text_top)}/{clean_text(text_bottom)}.jpg"
    elif text_bottom:
        url = f"https://api.memegen.link/images/{template_id}/_/{clean_text(text_bottom)}.jpg"
    else:
        url = f"https://api.memegen.link/images/{template_id}/_/_ .jpg".replace(" ", "_")
        
    logger.info(f"🔗 Финальный URL запроса: {url}")
    
    headers = {
        "User-Agent": "MaxBot/1.0 (https://github.com/MDeniska/max-bot)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 404:
            raise Exception(f"Шаблон '{template_id}' временно недоступен. Попробуй еще раз.")
        if response.status_code == 503:
            raise Exception("Сервис мемов перегружен. Попробуй через минуту.")
            
        response.raise_for_status()
        
        logger.info(f"✅ Мем успешно скачан ({len(response.content)} байт)")
        return response.content
        
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Ошибка сервиса мемов: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания мема: {e}")
        raise Exception("Не удалось создать мем. Попробуй написать текст короче или использовать другой разделитель.")


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
