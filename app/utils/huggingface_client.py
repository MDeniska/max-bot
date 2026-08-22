"""
Клиент для Hugging Face Inference API (Image-to-Image)
"""
import os
import logging
import io
from PIL import Image
from huggingface_hub import InferenceClient, InferenceTimeoutError

logger = logging.getLogger("huggingface")

HF_TOKEN = os.getenv("HF_TOKEN", "")

STYLE_PROMPTS = {
    "anime": "anime style, studio ghibli, vibrant colors, masterpiece, best quality, highly detailed",
    "cyberpunk": "cyberpunk style, neon lights, futuristic, highly detailed, 8k resolution, cinematic lighting",
    "oil": "classical oil painting, textured, masterpiece, museum quality, thick brushstrokes, classical art",
    "watercolor": "soft watercolor painting, artistic, gentle edges, pastel colors, soft lighting"
}

def generate_avatar(image_bytes: bytes, style: str) -> bytes:
    """Принимает байты изображения и стиль, возвращает байты обработанного изображения"""
    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["anime"])
    
    try:
        logger.info(f"🎨 Запрос к HF (модель: timbrooks/instruct-pix2pix), стиль: {style}")
        
        client = InferenceClient(model="timbrooks/instruct-pix2pix", token=HF_TOKEN)
        
        # 1. Открываем и конвертируем в RGB
        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 2. КРИТИЧЕСКИ ВАЖНО: Уменьшаем изображение, если оно слишком большое для API
        max_dimension = 1024
        if input_image.width > max_dimension or input_image.height > max_dimension:
            input_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            logger.info(f"📏 Изображение уменьшено для API до: {input_image.size}")
        else:
            logger.info(f"📏 Размер исходного изображения: {input_image.size}")
        
        # 3. Отправляем запрос (strength=0.7 сохраняет черты лица)
        result_image = client.image_to_image(
            input_image,
            prompt=prompt,
            strength=0.7,
            guidance_scale=7.5
        )
        
        # 4. Конвертируем результат в байты JPEG
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='JPEG', quality=90)
        
        logger.info("✅ Изображение успешно обработано Hugging Face!")
        return img_byte_arr.getvalue()
        
    except InferenceTimeoutError:
        logger.warning("⏳ Превышено время ожидания Hugging Face (модель 'просыпается').")
        raise Exception("Модель Hugging Face сейчас загружается на сервере. Пожалуйста, попробуй отправить фото еще раз через 30 секунд.")
    except Exception as e:
        error_details = str(e) if str(e) else "Неизвестная ошибка API (возможно, формат или размер файла не поддерживаются)"
        logger.error(f"❌ ДЕТАЛЬНАЯ ОШИБКА HUGGING FACE: {error_details}")
        raise Exception(f"Ошибка Hugging Face: {error_details}")
