"""
Клиент для Hugging Face Inference API (Image-to-Image)
Использует прямые запросы для максимальной стабильности и сохранения лица.
"""
import os
import logging
import io
import base64
import requests
from PIL import Image

logger = logging.getLogger("huggingface")

HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_ID = "timbrooks/instruct-pix2pix"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

STYLE_PROMPTS = {
    "anime": "make this person look like a high quality anime character, studio ghibli style, vibrant colors, masterpiece",
    "cyberpunk": "make this person look like a cyberpunk character, neon lights, futuristic, highly detailed, 8k resolution",
    "oil": "make this look like a classical oil painting, textured, masterpiece, museum quality, thick brushstrokes",
    "watercolor": "make this look like a soft watercolor painting, artistic, gentle edges, pastel colors"
}

def generate_avatar(image_bytes: bytes, style: str) -> bytes:
    """Принимает байты изображения и стиль, возвращает байты обработанного изображения"""
    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["anime"])
    
    try:
        logger.info(f"🎨 Запрос к HF (модель: {MODEL_ID}), стиль: {style}")
        
        # 1. Открываем и конвертируем в RGB
        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 2. КРИТИЧЕСКИ ВАЖНО: Уменьшаем до 512x512. 
        # Это предотвращает "молчаливые" сбои API из-за слишком большого размера файла
        max_dimension = 512
        if input_image.width > max_dimension or input_image.height > max_dimension:
            input_image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
        # Округляем до кратного 8 для совместимости с моделью
        width = (input_image.width // 8) * 8
        height = (input_image.height // 8) * 8
        input_image = input_image.resize((width, height), Image.Resampling.LANCZOS)
        logger.info(f"📏 Изображение подготовлено для API: {width}x{height}")
        
        # 3. Кодируем в base64
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format='JPEG', quality=90)
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # 4. Формируем payload. strength=0.7 означает: 70% нового стиля, 30% сохранения оригинала
        payload = {
            "inputs": img_base64,
            "parameters": {
                "prompt": prompt,
                "negative_prompt": "ugly, blurry, low quality, distorted, deformed, different face, mutated, extra limbs",
                "strength": 0.7,
                "guidance_scale": 7.5,
                "num_inference_steps": 25
            }
        }
        
        logger.info("📤 Отправка запроса на Hugging Face...")
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        
        # 5. Проверяем ответ
        if response.headers.get("content-type") == "application/json":
            error_data = response.json()
            error_msg = error_data.get("error", "Неизвестная ошибка сервера")
            logger.error(f"❌ ОШИБКА HUGGING FACE (JSON): {error_msg}")
            
            if "Model is loading" in error_msg:
                raise Exception("Модель Hugging Face сейчас просыпается. Пожалуйста, попробуй отправить фото еще раз через 20-30 секунд.")
            else:
                raise Exception(f"Ошибка API: {error_msg}")
        
        response.raise_for_status()
        
        logger.info("✅ Изображение успешно обработано Hugging Face!")
        return response.content
        
    except requests.exceptions.Timeout:
        raise Exception("Превышено время ожидания ответа от Hugging Face. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        raise Exception(f"Сбой генерации: {str(e)}")
