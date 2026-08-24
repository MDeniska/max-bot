"""
Клиент для генерации изображений
- Для генерации по тексту (txt2img): Stable Horde с моделью DreamShaper (высокое качество и точность)
- Для аватарок (img2img): Hugging Face (ждём переноса бота на nl14)
"""
import requests
import logging
import time
import os

logger = logging.getLogger("bot")

HORDE_API_URL = "https://stablehorde.net/api/v2"
HORDE_API_KEY = os.getenv("STABLE_HORDE_KEY", "xjnBHSR14-QkyOjJFPGM1Q")
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def translate_to_english(text: str) -> str:
    """Автоматически переводит текст с русского на английский"""
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "ru|en"}
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            translated = response.json().get("responseData", {}).get("translatedText")
            if translated:
                logger.info(f"🌐 Перевод: '{text}' -> '{translated}'")
                return translated
    except Exception as e:
        logger.warning(f"⚠️ Ошибка перевода, используем оригинал: {e}")
    return text


def generate_image_from_text(prompt: str, width: int = 512, height: int = 512) -> bytes:
    """Генерация картинки через Stable Horde с использованием модели DreamShaper"""
    
    # 1. Переводим запрос
    en_prompt = translate_to_english(prompt)
    
    # 2. Формируем ИДЕАЛЬНЫЙ промпт для DreamShaper
    # DreamShaper отлично понимает такие конструкции
    enhanced_prompt = (
        f"masterpiece, best quality, highly detailed, 8k resolution, photorealistic, "
        f"cinematic lighting, sharp focus, {en_prompt}"
    )
    
    # 3. Жесткий негативный промпт (запрещаем всё лишнее)
    negative_prompt = (
        "ugly, blurry, low quality, distorted, deformed, bad anatomy, bad hands, "
        "missing fingers, extra limbs, text, watermark, signature, frame, border, "
        "canvas, painting of, drawing of, illustration, human, person, girl, woman, cosplay"
    )
    
    logger.info(f"🎨 Stable Horde (DreamShaper): '{en_prompt[:50]}...'")
    
    headers = {
        "apikey": HORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "MaxBot:1.0.0:unknown:0.0.0"
    }
    
    # 4. Payload, который ГАРАНТИРОВАННО проходит по бесплатным лимитам (без 403 ошибки)
    payload = {
        "prompt": enhanced_prompt,
        "negative_prompt": negative_prompt,
        "params": {
            "sampler_name": "k_dpmpp_2m", # Лучший сэмплер для качества
            "cfg_scale": 7.5,
            "steps": 25,
            "width": width,
            "height": height,
            "karras": True # Делает картинку более чистой и детализированной
        },
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["DreamShaper"], # <-- ВОЛШЕБНАЯ МОДЕЛЬ
        "r2": True
    }
    
    return _submit_and_wait(headers, payload, max_wait_seconds=180) # 3 минуты максимум


def _submit_and_wait(headers, payload, max_wait_seconds=180):
    """Отправляет запрос и ждёт результат"""
    request_id = None
    try:
        response = requests.post(f"{HORDE_API_URL}/generate/async", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 403:
            error_data = response.json()
            logger.error(f"❌ Stable Horde: Не хватает кудо! {error_data.get('message')}")
            raise Exception("Сервису не хватает кредитов. Попробуйте более простой запрос.")
            
        if response.status_code != 202:
            logger.error(f"❌ Stable Horde: ошибка отправки: {response.status_code} - {response.text}")
            return None
        
        request_id = response.json().get("id")
        if not request_id:
            return None
            
        logger.info(f"✅ Stable Horde: запрос отправлен, ID: {request_id}")
        
        start_time = time.time()
        last_logged_queue = 0
        
        while time.time() - start_time < max_wait_seconds:
            time.sleep(3)
            try:
                check_response = requests.get(f"{HORDE_API_URL}/generate/check/{request_id}", headers=headers, timeout=10)
                if check_response.status_code != 200:
                    continue
                
                check_data = check_response.json()
                
                if check_data.get("faulted"):
                    logger.error("❌ Stable Horde: запрос отменён сервером (faulted)")
                    return None
                
                queue_pos = check_data.get("queue_position", 0)
                wait_time = check_data.get("wait_time", 0)
                if queue_pos > 0 and queue_pos != last_logged_queue:
                    logger.info(f"⏳ Stable Horde: в очереди. Позиция: {queue_pos}, время: {wait_time} сек.")
                    last_logged_queue = queue_pos
                
                if check_data.get("done"):
                    logger.info("✅ Stable Horde: генерация завершена! Забираем результат...")
                    status_response = requests.get(f"{HORDE_API_URL}/generate/status/{request_id}", headers=headers, timeout=30)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        generations = status_data.get("generations", [])
                        if generations:
                            img_url = generations[0].get("img")
                            img_response = requests.get(img_url, timeout=30)
                            if img_response.status_code == 200:
                                logger.info(f"✅ Stable Horde: картинка скачана ({len(img_response.content)} байт)")
                                return img_response.content
                    return None
            except Exception as e:
                logger.warning(f"⚠️ Stable Horde: ошибка при проверке: {e}")
                continue
                
        logger.error(f"❌ Stable Horde: таймаут ожидания")
        return None
    except Exception as e:
        logger.error(f"❌ Stable Horde исключение: {e}")
        raise e


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
