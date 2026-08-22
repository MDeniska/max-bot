"""
Клиент для Hugging Face Inference API (Image-to-Image)
"""
import os
import logging
import io
from PIL import Image
from huggingface_hub import InferenceClient, InferenceTimeoutError

logger = logging.getLogger("huggingface")

# Берем токен из переменных окружения. Если его там нет, используем твой (но лучше держать его в .env / настройках Bothost!)
HF_TOKEN = os.getenv("HF_TOKEN", "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")

# Промпты для разных стилей (оптимизированы для instruct-pix2pix)
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
        
        # Инициализируем клиент
        client = InferenceClient(model="timbrooks/instruct-pix2pix", token=HF_TOKEN)
        
        # Открываем изображение и ГАРАНТИРОВАННО конвертируем в RGB. 
        # Это критически важно, так как PNG с прозрачностью (RGBA) часто вызывают молчаливые ошибки в API.
        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        logger.info(f"📏 Размер исходного изображения: {input_image.size}")
        
        # strength=0.7 означает, что мы меняем стиль, но сохраняем 30% исходных черт лица.
        # Если лицо все равно меняется сильно, можно снизить до 0.6
        result_image = client.image_to_image(
            input_image,
            prompt=prompt,
            strength=0.7,
            guidance_scale=7.5
        )
        
        # Конвертируем результат обратно в байты JPEG для отправки в MAX
        img_byte_arr = io.BytesIO()
        result_image.save(img_byte_arr, format='JPEG', quality=90)
        
        logger.info("✅ Изображение успешно обработано Hugging Face!")
        return img_byte_arr.getvalue()
        
    except InferenceTimeoutError:
        logger.warning("⏳ Превышено время ожидания Hugging Face (модель 'просыпается').")
        raise Exception("Модель Hugging Face сейчас загружается на сервере. Пожалуйста, попробуй отправить фото еще раз через 30 секунд.")
    except Exception as e:
        # Логируем ПОЛНЫЙ и ПОДРОБНЫЙ текст ошибки, чтобы мы точно знали, что пошло не так
        error_details = str(e)
        logger.error(f"❌ ДЕТАЛЬНАЯ ОШИБКА HUGGING FACE: {error_details}")
        raise Exception(f"Ошибка Hugging Face: {error_details}")
