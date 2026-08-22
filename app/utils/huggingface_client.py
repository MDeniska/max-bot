"""
Клиент для Hugging Face Inference API (Image-to-Image)
"""
import os
import logging
import time
import requests
import io
from PIL import Image

logger = logging.getLogger("huggingface")

HF_TOKEN = os.getenv("HF_TOKEN", "")
# Бесплатная, но мощная модель для редактирования изображений по тексту
MODEL_ID = "timbrooks/instruct-pix2pix"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# Промпты для разных стилей
STYLE_PROMPTS = {
    "anime": "Make this person look like a high quality anime character, vibrant colors, studio ghibli style, masterpiece",
    "cyberpunk": "Make this person look like a cyberpunk character, neon lights, futuristic, highly detailed, 8k resolution",
    "oil": "Make this look like a classical oil painting, textured, masterpiece, museum quality, thick brushstrokes",
    "watercolor": "Make this look like a soft watercolor painting, artistic, gentle edges, pastel colors"
}

def generate_avatar(image_bytes: bytes, style: str) -> bytes:
    """Принимает байты изображения и стиль, возвращает байты обработанного изображения"""
    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["anime"])
    
    # Hugging Face может "спать". Делаем до 3 попыток с ожиданием
    for attempt in range(3):
        try:
            logger.info(f"🎨 Запрос к HF (попытка {attempt + 1}): стиль {style}...")
            response = requests.post(
                API_URL,
                headers=HEADERS,
                data=image_bytes,
                timeout=30
            )
            
            # Если модель "спит", HF вернет 503 и время ожидания в заголовке
            if response.status_code == 503:
                wait_time = int(response.headers.get("x-wait-for-model", 20))
                logger.warning(f"⏳ Модель просыпается. Ждем {wait_time} сек...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            
            # Конвертируем полученные байты в изображение и обратно в JPEG для надежности
            image = Image.open(io.BytesIO(response.content))
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=90)
            
            logger.info("✅ Изображение успешно обработано Hugging Face!")
            return img_byte_arr.getvalue()
            
        except requests.exceptions.Timeout:
            logger.warning("⏳ Превышено время ожидания ответа от HF.")
            if attempt < 2:
                time.sleep(5)
            else:
                raise Exception("Сервис Hugging Face не отвечает. Попробуйте позже.")
        except Exception as e:
            logger.error(f"❌ Ошибка Hugging Face: {e}")
            raise Exception(f"Не удалось обработать изображение: {str(e)}")
            
    raise Exception("Модель не смогла проснуться. Попробуйте еще раз через минуту.")
