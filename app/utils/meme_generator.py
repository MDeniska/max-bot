"""
Генератор мемов через memegen.link (Идеальный шрифт Impact, актуальные шаблоны)
Без ручного кодирования URL, чтобы избежать циклических редиректов.
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
    """Заменяет пробелы на подчеркивания, как требует memegen.link"""
    return "_".join(text.split())


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
        # Если разделителя нет, используем только нижний текст
        text_top = ""
        text_bottom = text.strip()

    logger.info(f"🎭 Генерация мема: верх='{text_top}', низ='{text_bottom}'")

    # 2. Выбираем случайный шаблон
    template_id = random.choice(TEMPLATES)
    
    # 3. Очищаем текст (пробелы -> подчеркивания). Пустой текст заменяем на "_"
    top_clean = clean_text(text_top) if text_top else "_"
    bottom_clean = clean_text(text_bottom) if text_bottom else "_"
    
    # 4. Формируем URL. Библиотека requests САМА корректно закодирует кириллицу.
    if text_top and text_bottom:
        url = f"https://api.memegen.link/images/{template_id}/{top_clean}/{bottom_clean}.jpg"
    else:
        url = f"https://api.memegen.link/images/{template_id}/{bottom_clean}.jpg"
        
    logger.info(f"🔗 URL мема: {url}")
    
    # 5. Добавляем User-Agent, чтобы нас не блокировали как бота
    headers = {
        "User-Agent": "MaxBot/1.0 (https://github.com/MDeniska/max-bot)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        # Проверка на множественные редиректы (на всякий случай)
        if len(response.history) > 5:
            logger.warning(f"⚠️ Множественные редиректы: {[r.status_code for r in response.history]}")
            
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
