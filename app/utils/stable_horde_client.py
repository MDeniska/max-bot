"""
Клиент для Stable Horde (AI Horde) - генерация и стилизация изображений
"""
import os
import logging
import time
import requests
import base64
import io
from PIL import Image

logger = logging.getLogger("stable_horde")

# Твой API ключ (дает приоритет в очереди)
API_KEY = os.getenv("STABLE_HORDE_KEY", "xjnBHSR14-QkyOjJFPGM1Q")
BASE_URL = "https://stablehorde.net/api/v2"

# Промпты для разных стилей (оптимизированы для Stable Diffusion)
STYLE_PROMPTS = {
    "anime": "masterpiece, best quality, anime style, studio ghibli, vibrant colors, highly detailed, 1girl/1boy",
    "cyberpunk": "masterpiece, best quality, cyberpunk style, neon lights, futuristic, highly detailed, 8k resolution, cinematic lighting",
    "oil": "masterpiece, best quality, oil painting, textured, museum quality, thick brushstrokes, classical art style",
    "watercolor": "masterpiece, best quality, watercolor painting, artistic, gentle edges, pastel colors, soft lighting"
}

def generate_avatar(image_bytes: bytes, style: str) -> bytes:
    """Генерирует аватар через Stable Horde (img2img)"""
    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["anime"])
    
    # Кодируем исходное изображение в base64
    img_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "prompt": prompt,
        "params": {
            "sampler_name": "k_dpmpp_2m",
            "cfg_scale": 7.5,
            "denoising_strength": 0.65, # 0.65 сохраняет черты лица, но меняет стиль
            "seed": "0",
            "height": 512,
            "width": 512,
            "karras": True,
            "hires_fix": False
        },
        "r2": True, # Возвращать результат напрямую через быстрый CDN
        "shared": False,
        "trusted_workers": True,
        "source_image": img_base64,
        "source_processing": "img2img",
        "models": ["stable_diffusion"] # Можно указать конкретные модели, например "Anything V5" для аниме
    }
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "Client-Agent": "MaxBot:1.0.0:unknown:0.0.0"
    }
    
    try:
        logger.info(f"🎨 Отправка запроса на генерацию в Stable Horde (стиль: {style})...")
        
        # 1. Инициируем генерацию
        response = requests.post(f"{BASE_URL}/generate/async", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "message" in result:
            raise Exception(f"Stable Horde вернул ошибку: {result['message']}")
            
        generation_id = result["id"]
        logger.info(f"✅ Задача создана, ID: {generation_id}. Ожидаем результат...")
        
        # 2. Опрашиваем статус (максимум 60 попыток по 3 секунды = 3 минуты)
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(3)
            
            check_response = requests.get(f"{BASE_URL}/generate/check/{generation_id}", headers=headers, timeout=10)
            check_response.raise_for_status()
            check_data = check_response.json()
            
            if check_data.get("done"):
                logger.info("✅ Генерация завершена! Забираем результат...")
                status_response = requests.get(f"{BASE_URL}/generate/status/{generation_id}", headers=headers, timeout=10)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if "generations" in status_data and len(status_data["generations"]) > 0:
                    img_url = status_data["generations"][0]["img"]
                    
                    # Скачиваем готовое изображение
                    img_response = requests.get(img_url, timeout=15)
                    img_response.raise_for_status()
                    
                    # Конвертируем в JPEG для надежности перед отправкой в MAX
                    image = Image.open(io.BytesIO(img_response.content))
                    img_byte_arr = io.BytesIO()
                    # Если изображение в режиме RGBA (с прозрачностью), конвертируем в RGB
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    image.save(img_byte_arr, format='JPEG', quality=90)
                    
                    logger.info("✅ Изображение успешно получено из Stable Horde!")
                    return img_byte_arr.getvalue()
                else:
                    raise Exception("Stable Horde не вернул изображение в статусе.")
            
        raise Exception("Превышено время ожидания генерации в Stable Horde (3 минуты).")
        
    except Exception as e:
        logger.error(f"❌ Ошибка Stable Horde: {e}")
        raise Exception(f"Не удалось обработать изображение: {str(e)}")
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
            "post_processing": ["GFPGAN"] # Улучшает детали, если вдруг сгенерировались лица
        },
        "nsfw": False,
        "censor_nsfw": False,
        "models": ["AlbedoBase XL (SDXL)"],
        "r2": True
    }
    
    return _submit_and_wait(headers, payload, max_wait_seconds=300)
