"""
Клиент для работы со Stable Horde API
Оптимизирован для сохранения лица в img2img и генерации по тексту (txt2img)
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
    """Генерирует аватар с максимальным сохранением черт лица (img2img)"""
    style_prompts = {
        "anime": "masterpiece, best quality, anime style, studio ghibli, vibrant colors, highly detailed",
        "cyberpunk": "masterpiece, best quality, cyberpunk style, neon lights, futuristic, 8k resolution",
        "oil": "masterpiece, best quality, classical oil painting, textured, museum quality, thick brushstrokes",
        "watercolor": "masterpiece, best quality, soft watercolor painting, artistic, gentle edges, pastel colors"
    }
    
    base_prompt = style_prompts.get(style, style_prompts["anime"])
    final_prompt = f"same person, exact same face, identical facial features, {base_prompt}"
    
    logger.info(f"🎨 Stable Horde: img2img с сохранением лица (стиль: {style})")
    
    headers = {
        "apikey": HORDE_API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "MaxBot:1.0.0:unknown:0.0.0"
    }
    
    payload = {
        "prompt": final_prompt,
        "negative_prompt": FACE_PRESERVATION_NEGATIVE,
        "params": {
            "sampler_name": "k_dpmpp_2m",
            "cfg_scale": 9.0,
            "steps": 30,
            "width": 768,
            "height": 768,
            "denoising_strength": 0.55, # Ключевой параметр для сохранения лица
            "karras": True,
            "post_processing": ["GFPGAN"] # Улучшение черт лица
        },
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["AlbedoBase XL (SDXL)"],
        "source_image": source_image_base64,
        "source_processing": "img2img",
        "r2": True
    }
    
    return _submit_and_wait(headers, payload, max_wait_seconds=300)


def generate_image_from_text(prompt: str, width: int = 768, height: int = 768) -> bytes:
    """Генерация картинки по текстовому описанию (txt2img)"""
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
            "sampler_name": "k_dpmpp_2m",
            "cfg_scale": 8.0,
            "steps": 30,
            "width": width,
            "height": height,
            "karras": True,
            "post_processing": ["GFPGAN"]
        },
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["AlbedoBase XL (SDXL)"],
        "r2": True
    }
    
    return _submit_and_wait(headers, payload, max_wait_seconds=300)


def _submit_and_wait(headers, payload, max_wait_seconds=300):
    """Отправляет запрос и ждёт результат"""
    request_id = None
    try:
        response = requests.post(f"{HORDE_API_URL}/generate/async", headers=headers, json=payload, timeout=30)
        if response.status_code != 202:
            logger.error(f"❌ Stable Horde: ошибка отправки: {response.status_code} - {response.text}")
            return None
        
        request_id = response.json().get("id")
        if not request_id:
            return None
            
        logger.info(f"✅ Stable Horde: запрос отправлен, ID: {request_id}")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            time.sleep(3)
            try:
                check_response = requests.get(f"{HORDE_API_URL}/generate/check/{request_id}", headers=headers, timeout=10)
                if check_response.status_code != 200:
                    continue
                
                check_data = check_response.json()
                if check_data.get("faulted"):
                    logger.error("❌ Stable Horde: запрос отменён сервером")
                    return None
                
                if check_data.get("done"):
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
            except Exception:
                continue
        logger.error("❌ Stable Horde: таймаут ожидания")
        return None
    except Exception as e:
        logger.error(f"❌ Stable Horde исключение: {e}")
        return None


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
