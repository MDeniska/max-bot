"""
Клиент для работы со Stable Horde API (Оптимизирован для бесплатных лимитов)
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

FACE_PRESERVATION_NEGATIVE = (
    "different face, changed face, altered facial features, different person, "
    "mutated face, distorted face, ugly, blurry, low quality, deformed, bad anatomy, "
    "extra limbs, disfigured, watermark, text, signature"
)

def generate_avatar_from_image(source_image_base64: str, style: str) -> bytes:
    """Генерирует аватар с сохранением черт лица (img2img, облегченный)"""
    style_prompts = {
        "anime": "masterpiece, best quality, anime style, studio ghibli, vibrant colors, highly detailed",
        "cyberpunk": "masterpiece, best quality, cyberpunk style, neon lights, futuristic, 8k resolution",
        "oil": "masterpiece, best quality, classical oil painting, textured, museum quality, thick brushstrokes",
        "watercolor": "masterpiece, best quality, soft watercolor painting, artistic, gentle edges, pastel colors"
    }
    
    base_prompt = style_prompts.get(style, style_prompts["anime"])
    final_prompt = f"same person, exact same face, identical facial features, {base_prompt}"
    
    logger.info(f"🎨 Stable Horde: img2img (стиль: {style})")
    
    headers = {
        "apikey": HORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "MaxBot:1.0.0:unknown:0.0.0"
    }
    
    payload = {
        "prompt": final_prompt,
        "negative_prompt": FACE_PRESERVATION_NEGATIVE,
        "params": {
            "sampler_name": "k_euler",       # Более быстрый и дешевый сэмплер
            "cfg_scale": 7.0,
            "steps": 20,                     # Уменьшено для бесплатного лимита
            "width": 512,                    # Уменьшено до 512 (ниже порога 700x700)
            "height": 512,
            "denoising_strength": 0.55,      # Сохраняет лицо
            "karras": False                  # Отключено для экономии кудо
        },
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["stable_diffusion"],
        "source_image": source_image_base64,
        "source_processing": "img2img",
        "r2": True
    }
    
    return _submit_and_wait(headers, payload, max_wait_seconds=300)


def generate_image_from_text(prompt: str, width: int = 512, height: int = 512) -> bytes:
    """Генерация картинки по тексту (txt2img, облегченная)"""
    logger.info(f"🎨 Stable Horde: txt2img '{prompt[:50]}...'")
    
    headers = {
        "apikey": HORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "MaxBot:1.0.0:unknown:0.0.0"
    }
    
    payload = {
        "prompt": f"masterpiece, best quality, highly detailed, {prompt}",
        "negative_prompt": "ugly, blurry, low quality, distorted, deformed, bad anatomy, watermark, text",
        "params": {
            "sampler_name": "k_euler",
            "cfg_scale": 7.0,
            "steps": 20,
            "width": width,
            "height": height,
            "karras": False
        },
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["stable_diffusion"],
        "r2": True
    }
    
    return _submit_and_wait(headers, payload, max_wait_seconds=300)


def _submit_and_wait(headers, payload, max_wait_seconds=300):
    """Отправляет запрос и ждёт результат"""
    request_id = None
    try:
        response = requests.post(f"{HORDE_API_URL}/generate/async", headers=headers, json=payload, timeout=30)
        
        # ЛОВИМ ОШИБКУ НЕХВАТКИ КУДО ПРЯМО ЗДЕСЬ
        if response.status_code == 403:
            error_data = response.json()
            logger.error(f"❌ Stable Horde: Не хватает кудо! {error_data.get('message')}")
            raise Exception("Сервису не хватает кредитов (kudos) для этого запроса. Попробуйте более простой запрос или обновите ключ API.")
            
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
        # Пробрасываем исключение дальше, чтобы бот мог показать его пользователю
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
