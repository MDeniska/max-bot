"""
Обработчики текстовых сообщений и фото
"""
import logging
import json
import base64
import requests
from flask import jsonify

import database as db
from app.utils import max_api
from app.utils import stable_horde_client
from app import keyboards
from app import messages

logger = logging.getLogger("bot")


def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        
        # 1. Защита от дубликатов
        message_id = message.get('id') or message.get('message_id') or data.get('update_id')
        if message_id:
            if db.is_message_processed(message_id):
                return jsonify({"ok": True}), 200
            db.mark_message_processed(message_id)
        
        # 2. Извлечение данных
        text = message.get('body', {}).get('text', '').strip()
        attachments = message.get('body', {}).get('attachments', [])
        
        incoming_image_url = None
        for att in attachments:
            if att.get('type') == 'image':
                payload = att.get('payload', {})
                incoming_image_url = payload.get('url')
                break
                
        if not text and not incoming_image_url:
            return jsonify({"ok": True}), 200
        
        state = db.get_user_state(user_id)
        logger.info(f"📩 Текст: '{text[:20]}...' | Фото: {bool(incoming_image_url)} | State: '{state}' | user_id={user_id}")
        
        if user_id and chat_id:
            db.save_chat_id(user_id, chat_id)
        
        # 3. Глобальная команда /start
        if text.lower() == "/start":
            db.set_user_state(user_id, 'idle')
            max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_keyboard())
            return jsonify({"ok": True}), 200
        
        # 4. СЦЕНАРИЙ: AI АВАТАРКИ (Ожидаем фото)
        if state == 'avatar_waiting_photo':
            if incoming_image_url:
                max_api.send_message(chat_id, "🎨 Получил фото! Магия начинается... Это займет 20-40 секунд.")
                
                temp_data = db.get_temp_data(user_id) or "style:anime"
                style_key = temp_data.replace("style:", "")
                
                try:
                    logger.info(f"📥 Скачиваем исходное фото: {incoming_image_url}")
                    resp = requests.get(incoming_image_url, timeout=15)
                    resp.raise_for_status()
                    original_bytes = resp.content
                    
                    logger.info(f"🎨 Отправляем в Stable Horde (стиль: {style_key})...")
                    source_image_base64 = base64.b64encode(original_bytes).decode('utf-8')
                    
                    processed_bytes = stable_horde_client.generate_avatar_from_image(
                        source_image_base64=source_image_base64,
                        style=style_key
                    )
                    
                    if not processed_bytes:
                        raise Exception("Stable Horde не вернул изображение")
                    
                    logger.info("📤 Загружаем результат в MAX API...")
                    new_token = stable_horde_client.upload_to_max_api(processed_bytes)
                    
                    if new_token:
                        max_api.send_image_message(
                            chat_id, 
                            f"✨ Готово! Твоя аватарка в стиле **{style_key.capitalize()}**.\n\nХочешь попробовать другой стиль? Нажми 'Главное меню'!", 
                            new_token
                        )
                    else:
                        raise Exception("Не удалось загрузить результат в MAX API")
                        
                    db.set_user_state(user_id, 'idle')
                    db.save_temp_data(user_id, "")
                    logger.info("✅ Сценарий аватарки успешно завершен")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации аватара: {e}")
                    max_api.send_message(
                        chat_id, 
                        f"❌ Упс, произошла ошибка: {str(e)}\n\n💡 *Совет:* Попробуй отправить другое, более четкое фото, или выбери другой стиль.", 
                        attachments=keyboards.get_back_keyboard()
                    )
                    db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Пожалуйста, отправь именно фотографию (нажми на скрепку 📎).", attachments=keyboards.get_back_keyboard())
        
        # 5. СЦЕНАРИЙ: ГЕНЕРАЦИЯ КАРТИНОК ПО ТЕКСТУ
        elif state == 'waiting_image_prompt':
            if text:
                max_api.send_message(chat_id, "🎨 Магия начинается... Рисую по твоему описанию. Это займет 20-40 секунд.")
                
                try:
                    processed_bytes = stable_horde_client.generate_image_from_text(
                        prompt=text,
                        width=768,
                        height=768
                    )
                    
                    if not processed_bytes:
                        raise Exception("Сервис генерации не вернул изображение. Попробуй изменить запрос.")
                    
                    new_token = stable_horde_client.upload_to_max_api(processed_bytes)
                    
                    if new_token:
                        max_api.send_image_message(
                            chat_id, 
                            f"✨ Готово! Вот что получилось по запросу:\n\n*{text}*", 
                            new_token
                        )
                    else:
                        raise Exception("Не удалось загрузить результат в MAX API")
                        
                    db.set_user_state(user_id, 'idle')
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации картинки: {e}")
                    max_api.send_message(
                        chat_id, 
                        f"❌ Упс, ошибка: {str(e)}\n\nПопробуй описать картинку другими словами.", 
                        attachments=keyboards.get_back_keyboard()
                    )
                    db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Пожалуйста, напиши описание картинки текстом.", attachments=keyboards.get_back_keyboard())
        
        # 6. СОСТОЯНИЕ ПО УМОЛЧАНИЮ
        else:
            max_api.send_message(chat_id, messages.UNKNOWN_COMMAND, attachments=keyboards.get_main_keyboard())
        
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКОЕ ИСКЛЮЧЕНИЕ в handle_message: {e}", exc_info=True)
        return jsonify({"ok": True}), 200
