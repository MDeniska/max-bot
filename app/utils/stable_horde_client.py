"""
Клиент для генерации изображений
Для аватарок (img2img) готовим Hugging Face (ждём переноса на nl14)
Для генерации по тексту (txt2img) используем быстрый и качественный Pollinations.ai (SDXL/Flux)
"""
import requests
import logging
import time
import os
import urllib.parse
import random

logger = logging.getLogger("bot")

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))

FACE_PRESERVATION_NEGATIVE = (
    "different face, changed face, altered facial features, different person, "
    "mutated face, distorted face, ugly, blurry, low quality, deformed, bad anatomy, "
    "extra limbs, disfigured, watermark, text, signature"
)

def translate_to_english(text: str) -> str:
    """Автоматически переводит текст с русского на английский для лучшего качества"""
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "ru|en"}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            translated = response.json().get("responseData", {}).get("translatedText")
            if translated:
                logger.info(f"🌐 Перевод промпта: '{text}' -> '{translated}'")
                return translated
    except Exception as e:
        logger.warning(f"⚠️ Не удалось перевести промпт, используем оригинал: {e}")
    return text


def generate_avatar_from_image(source_image_base64: str, style: str) -> bytes:
    """Генерирует аватар с сохранением черт лица (пока не работает из-за DNS на nsk7, ждем nl14)"""
    # Этот код останется здесь, чтобы заработать, как только Bothost перенесет бота на nl14
    logger.info("⚠️ Функция аватарок ожидает переноса сервера на nl14 для доступа к Hugging Face")
    raise Exception("Сервис аватарок временно недоступен (ошибка сети хостинга). Попробуйте через 10 минут или напишите админу.")


def generate_image_from_text(prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    """Генерация картинки по тексту через Pollinations.ai (быстро, бесплатно, высокое качество SDXL/Flux)"""
    
    # 1. Переводим запрос на английский
    en_prompt = translate_to_english(prompt)
    
    # 2. Усиливаем промпт для максимального качества и запрета "картин в рамке"
    enhanced_prompt = f"{en_prompt}, masterpiece, best quality, highly detailed, 8k resolution, photorealistic, vivid colors, full body shot, no frames, no borders, no canvas, standalone subject"
    
    # 3. Кодируем промпт для URL и добавляем случайный seed для разнообразия
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    seed = random.randint(1, 999999)
    
    # 4. Формируем URL. model=flux дает потрясающие результаты для сложных запросов
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
    
    logger.info(f"🎨 Генерация через Pollinations.ai (Flux)...")
    
    try:
        # Скачиваем картинку напрямую (таймаут 60 сек, так как генерация может занять 5-15 сек)
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        logger.info(f"✅ Картинка успешно получена ({len(response.content)} байт)")
        return response.content
        
    except requests.exceptions.Timeout:
        raise Exception("Превышено время ожидания генерации. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"❌ Ошибка генерации через Pollinations: {e}")
        raise Exception(f"Не удалось сгенерировать изображение: {e}")


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
        
        files = {"data": ("image.jpg", image_bytes, "image/jpeg")}
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
