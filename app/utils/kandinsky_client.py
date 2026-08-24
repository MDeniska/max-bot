"""
Клиент для генерации изображений через Sber Kandinsky (через Hugging Face API)
Нативно поддерживает русский язык!
"""
import os
import logging
import requests

logger = logging.getLogger("bot")

HF_TOKEN = os.getenv("HF_TOKEN", "")
# Используем официальную модель Kandinsky 2.2 от Сбера (ai-forever)
MODEL_ID = "ai-forever/kandinsky-2.2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}


def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    """Генерирует картинку по русскоязычному промпту через Kandinsky"""
    
    logger.info(f"🎨 Kandinsky: генерация по запросу '{prompt[:50]}...'")
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": width,
            "height": height,
            "num_inference_steps": 30,
            "guidance_scale": 7.5
        }
    }
    
    try:
        # Таймаут 60 секунд, так как генерация может занять время
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        
        # Проверяем, не вернул ли сервер ошибку в формате JSON
        if response.headers.get("content-type") == "application/json":
            error_data = response.json()
            error_msg = error_data.get("error", "Неизвестная ошибка")
            logger.error(f"❌ ОШИБКА KANDINSKY (JSON): {error_msg}")
            
            if "Model is loading" in error_msg:
                raise Exception("Модель Кандинского сейчас просыпается. Пожалуйста, попробуй отправить запрос еще раз через 20-30 секунд.")
            else:
                raise Exception(f"Ошибка API: {error_msg}")
        
        response.raise_for_status()
        
        logger.info(f"✅ Kandinsky: картинка успешно получена ({len(response.content)} байт)")
        return response.content
        
    except requests.exceptions.Timeout:
        raise Exception("Превышено время ожидания ответа от Кандинского. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА KANDINSKY: {str(e)}")
        raise Exception(f"Сбой генерации: {str(e)}")


def upload_to_max_api(image_bytes):
    """Загружает байты картинки на MAX API и возвращает token"""
    BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
    CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))
    
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
        files = {"data": ("kandinsky.jpg", image_bytes, "image/jpeg")}
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
