"""
Автономный генератор мемов с помощью Pillow
Работает мгновенно, без внешних API, с поддержкой кириллицы и обводкой текста.
"""
import requests
import logging
import random
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("bot")

# Надежные URL популярных шаблонов мемов (Imgflip)
TEMPLATES = [
    "https://i.imgflip.com/30b1gx.jpg",  # Drake Hotline Bling
    "https://i.imgflip.com/1ur9b0.jpg",  # Distracted Boyfriend
    "https://i.imgflip.com/261o3j.jpg",  # Buff Doge vs. Cheems
    "https://i.imgflip.com/4t0m5.jpg",   # Success Kid
    "https://i.imgflip.com/1g8my4.jpg",  # Two Buttons
    "https://i.imgflip.com/26am.jpg",    # Ancient Aliens
]

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
CERT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../minifry_certs.pem"))


def get_font(size=40):
    """Пытается загрузить шрифт с поддержкой кириллицы из стандартных путей Linux"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    logger.warning("⚠️ Кириллический шрифт не найден, используется стандартный")
    return ImageFont.load_default()


def generate_meme(text: str) -> bytes:
    """Генерирует мем локально с помощью Pillow"""
    
    # 1. Умное разделение текста: ищем слэш, тире или вертикальную черту
    separators = ['/', '|', '-', '—']
    split_char = None
    for sep in separators:
        if sep in text:
            split_char = sep
            break
            
    if split_char:
        parts = text.split(split_char, 1)
        text_top = parts[0].strip()
        text_bottom = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Если разделителя нет, разбиваем длинный текст пополам для баланса
        words = text.split()
        mid = len(words) // 2
        text_top = " ".join(words[:mid]) if mid > 0 else "Когда"
        text_bottom = " ".join(words[mid:]) if mid < len(words) else text

    logger.info(f"🎭 Генерация мема: верх='{text_top}', низ='{text_bottom}'")

    # 2. Выбираем случайный шаблон
    template_url = random.choice(TEMPLATES)
    
    try:
        response = requests.get(template_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания шаблона: {e}")
        raise Exception("Не удалось загрузить шаблон мема. Попробуй еще раз.")

    # 3. Рисуем текст
    draw = ImageDraw.Draw(img)
    font = get_font(size=40)
    
    def draw_text_with_outline(position, text, font, fill="white", outline="black"):
        # Рисуем обводку (смещение на 1-2 пикселя во все стороны)
        for adj in range(-2, 3):
            for opp in range(-2, 3):
                if adj == 0 and opp == 0:
                    continue
                draw.text((position[0]+adj, position[1]+opp), text, font=font, fill=outline)
        # Рисуем основной белый текст поверх обводки
        draw.text(position, text, font=font, fill=fill)

    width, height = img.size
    
    # Рисуем верхний текст (по центру)
    if text_top:
        bbox = draw.textbbox((0, 0), text_top.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        x_top = max(10, (width - text_width) // 2)
        draw_text_with_outline((x_top, 15), text_top.upper(), font)

    # Рисуем нижний текст (по центру, внизу)
    if text_bottom:
        bbox = draw.textbbox((0, 0), text_bottom.upper(), font=font)
        text_width = bbox[2] - bbox[0]
        x_bottom = max(10, (width - text_width) // 2)
        y_bottom = height - 55
        draw_text_with_outline((x_bottom, y_bottom), text_bottom.upper(), font)

    # 4. Сохраняем в байты
    output = BytesIO()
    img.save(output, format="JPEG", quality=90)
    logger.info(f"✅ Мем успешно сгенерирован ({len(output.getvalue())} байт)")
    return output.getvalue()


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
        files = {"data": ("meme.jpg", image_bytes, "image/jpeg")}
        file_response = requests.post(upload_url, files=files, timeout=30)
        
        if file_response.status_code != 200:
            logger.error(f"❌ MAX API: ошибка загрузки файла: {file_response.text}")
            return None
        
        file_data = file_response.json()
        photos = file_data.get("photos", {})
        if photos:
            first_photo_key = next(iter(photos.keys()))
            token = photos[first_photo_key].get("token")
            logger.info(f"✅ Мем загружен на MAX API, token: {token[:20]}...")
            return token
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки на MAX API: {e}")
        return None
