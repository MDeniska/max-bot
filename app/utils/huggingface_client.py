"""
Клиент для Hugging Face Inference API (Image-to-Image)
Использует прямые запросы для максимальной стабильности и прозрачности ошибок.
"""
import os
import logging
import io
import base64
import requests
from PIL import Image

logger = logging.getLogger("huggingface")

HF_TOKEN = os.getenv("HF_TOKEN", "")

# Используем самую стабильную модель на бесплатном API
MODEL_ID = "runwayml/stable-diffusion-v1-5"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

# Промпты, усиленные для сохранения черт лица
STYLE_PROMPTS = {
    "anime": "masterpiece, best quality, anime style, studio ghibli, vibrant colors, highly detailed, 1girl/1boy, same face, same person",
    "cyberpunk": "masterpiece, best quality, cyberpunk style, neon lights, futuristic, highly detailed, 8k resolution, cinematic lighting, same face, same person",
    "oil": "masterpiece, best quality, classical oil painting, textured, museum quality, thick brushstrokes, classical art, same face, same person",
    "watercolor": "masterpiece, best quality, soft watercolor painting, artistic, gentle edges, pastel colors, soft lighting, same face, same person"
}

def generate_avatar(image_bytes: bytes, style: str) -> bytes:
    """Принимает байты изображения и стиль, возвращает байты обработанного изображения"""
    prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["anime"])
    
    try:
        logger.info(f"🎨 Запрос к HF (модель: {MODEL_ID}), стиль: {style}")
        
        # 1. Открываем и конвертируем в RGB
        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # 2. Приводим к размеру, кратному 64 (требование Stable Diffusion), макс 768x768
        max_dim = 768
        if input_image.width > max_dim or input_image.height > max_dim:
            input_image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            
        # Округляем до кратного 64 для идеальной совместимости
        width = (input_image.width // 64) * 64
        height = (input_image.height // 64) * 64
        input_image = input_image.resize((width, height), Image.Resampling.LANCZOS)
        logger.info(f"📏 Изображение подготовлено для API: {width}x{height}")
        
        # 3. Кодируем в base64 для отправки в JSON
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format='JPEG', quality=90)
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # 4. Формируем payload для img2img
        payload = {
            "inputs": img_base64,
            "parameters": {
                "prompt": prompt,
                "negative_prompt": "ugly, blurry, low quality, distorted, deformed, different face, changed face, mutated, extra limbs",
                "strength": 0.65,       # 0.65 сохраняет лицо, но меняет стиль
                "guidance_scale": 7.5,
                "num_inference_steps": 30
            }
        }
        
        logger.info("📤 Отправка запроса на Hugging Face...")
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        
        # 5. Проверяем ответ
        if response.headers.get("content-type") == "application/json":
            # Если пришел JSON, значит это ошибка от сервера HF
            error_data = response.json()
            error_msg = error_data.get("error", "Неизвестная ошибка сервера")
            logger.error(f"❌ ОШИБКА HUGGING FACE (JSON): {error_msg}")
            
            if "Model is loading" in error_msg:
                raise Exception("Модель Hugging Face сейчас просыпается. Пожалуйста, попробуй отправить фото еще раз через 20-30 секунд.")
            else:
                raise Exception(f"Ошибка API: {error_msg}")
        
        response.raise_for_status()
        
        # Если всё хорошо, в ответе приходят байты картинки
        logger.info("✅ Изображение успешно обработано Hugging Face!")
        return response.content
        
    except requests.exceptions.Timeout:
        raise Exception("Превышено время ожидания ответа от Hugging Face. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        raise Exception(f"Сбой генерации: {str(e)}")
