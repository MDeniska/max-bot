"""
Генератор мемов через memegen.link (Идеальный шрифт Impact, актуальные шаблоны)
Использует query parameters (?text[]=...) для 100% надежной работы с кириллицей без редиректов.
"""
import requests
import logging
import random
import os

logger = logging.getLogger("bot")

# Актуальные и популярные шаблоны (ID из memegen.link)
TEMPLATES = [
    "drake",             # Drake Hotline Bling
    "distracted",        # Distracted Boyfriend
    "change_my_mind",    # Change My Mind
    "is_this",           # Is this a pigeon?
    "two_buttons",       # Two Buttons (Daily Struggle)
    "left_exit_12",      # Left Exit 12 Off Ramp
    "success",           # Success Kid
    "roll_safe",         # Roll Safe (Think about it)
    "uno_reverse",       # Uno Reverse Card
    "always_has_been"    # Always Has Been (Astronaut)
]

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def clean_text(text: str) -> str:
    """Заменяет пробелы на подчеркивания для корректного рендеринга в мемах"""
    return text.replace(" ", "_")


def generate_meme(text: str) -> bytes:
    """Генерирует мем через memegen.link с использованием query parameters"""
    
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
        # Если разделителя нет, используем только нижний текст
        text_top = ""
        text_bottom = text.strip()

    logger.info(f"🎭 Генерация мема: верх='{text_top}', низ='{text_bottom}'")

    # 2. Выбираем случайный шаблон
    template_id = random.choice(TEMPLATES)
    
    # 3. Формируем базовый URL (БЕЗ текста в пути!)
    url = f"https://api.memegen.link/images/{template_id}.jpg"
    
    # 4. Формируем параметры запроса. requests САМ корректно закодирует кириллицу здесь!
    if text_top and text_bottom:
        params = {"text[]": [clean_text(text_top), clean_text(text_bottom)]}
    elif text_bottom:
        params = {"text[]": clean_text(text_bottom)}
    else:
        params = {"text[]": "_"}
        
    logger.info(f"🔗 Запрос к мем-генератору с params: {params}")
    
    # 5. Добавляем User-Agent для надежности
    headers = {
        "User-Agent": "MaxBot/1.0 (https://github.com/MDeniska/max-bot)"
    }
    
    try:
        # Передаем params. requests превратит это в ?text%5B%5D=%D0%A1%D1%83%D1%81%D0%BB%D0%B8%D0%BA_%D0%BF%D0%BE%D0%BB%D0%B5%D1%82%D0%B5%D0%BB
        # Это 100% валидный запрос, который НЕ вызывает редиректы.
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 503:
            raise Exception("Сервис мемов временно перегружен. Попробуй через минуту.")
        response.raise_for_status()
        
        logger.info(f"✅ Мем успешно скачан ({len(response.content)} байт)")
        return response.content
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            raise Exception("Слишком длинный текст для мема. Напиши короче!")
        raise Exception(f"Ошибка сервиса мемов: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания мема: {e}")
        raise Exception("Не удалось создать мем. Попробуй другой текст или шаблон.")


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
