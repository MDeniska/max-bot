"""
Клиент для Hugging Face Inference API (Image-to-Image)
"""
import os
import logging
import io
from PIL import Image
from huggingface_hub import InferenceClient

logger = logging.getLogger("huggingface")

HF_TOKEN = os.getenv("HF_TOKEN", "")

# Промпты для разных стилей (адаптированы под instruct-pix2pix)
STYLE_PROMPTS = {
    "anime": "anime style, studio ghibli, vibrant colors, masterpiece, best quality, highly detailed",
    "cyberpunk": "cyberpunk style, neon lights, futuristic, highly detailed, 8k resolution, cinematic lighting",
    "oil": "oil painting, textured, masterpiece, museum quality, thick brushstrokes, classical art",
    "watercolor": "watercolor painting, artistic, gentle edges, pastel colors, soft lighting"
}

def generate_avatar(image_bytes: bytes, style: str) -> bytes:
    """Принимает байты изображения и стиль, возвращает байты обработанного изображения"""
    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["anime"])
    
    try:
        logger.info(f"🎨 Запрос к HF через InferenceClient: стиль {style}...")
        
        # Официальный клиент часто лучше справляется с сетевыми нюансами хостингов
        client = InferenceClient(model="timbrooks/instruct-pix2pix", token=HF_TOKEN)
        
        # Конвертируем полученные байты в объект PIL Image, который требует клиент
        input_image = Image.open(io.BytesIO(image_bytes))
        
        # Выполняем преобразование
        # strength=0.8 означает сильное изменение стиля с сохранением черт
        result_image = client.image_to_image(
            input_image,
            prompt=prompt,
            strength=0.8,
            guidance_scale=7.5
        )
        
        # Конвертируем результат обратно в байты JPEG для отправки в MAX
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='JPEG', quality=90)
        
        logger.info("✅ Изображение успешно обработано Hugging Face!")
        return img_byte_arr.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Ошибка Hugging Face: {e}")
        raise Exception(f"Не удалось обработать изображение: {str(e)}")
