"""
Обработчики текстовых сообщений и фото
"""
import logging
from flask import jsonify

import database as db
from app.utils import max_api
from app.utils import huggingface_client
from app import keyboards
from app import messages

logger = logging.getLogger("bot")


def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        
        message_id = message.get('id') or message.get('message_id') or data.get('update_id')
        if message_id:
            if db.is_message_processed(message_id):
                logger.info(f"🔁 Дубликат сообщения {message_id} — пропускаем")
                return jsonify({"ok": True}), 200
            db.mark_message_processed(message_id)
        
        text = message.get('body', {}).get('text', '').strip()
        attachments = message.get('body', {}).get('attachments', [])
        
        incoming_image_token = None
        for att in attachments:
            if att.get('type') == 'image':
                incoming_image_token = att.get('payload', {}).get('token')
                break
        
        if not text and not incoming_image_token:
            return jsonify({"ok": True}), 200
        
        state = db.get_user_state(user_id)
        logger.info(f"📩 Текст: '{text[:20]}...' | Фото: {bool(incoming_image_token)} | State: '{state}' | user_id={user_id}")
        
        if user_id and chat_id:
            db.save_chat_id(user_id, chat_id)
        
        # --- ГЛОБАЛЬНАЯ КОМАНДА /start ---
        if text.lower() == "/start":
            db.set_user_state(user_id, 'idle')
            max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_keyboard())
            return jsonify({"ok": True}), 200
        
        # --- СЦЕНАРИЙ: AI АВАТАРКИ (Ждем фото) ---
        if state == 'avatar_waiting_photo':
            if incoming_image_token:
                max_api.send_message(chat_id, "🎨 Получил фото! Магия начинается... Это займет 15-40 секунд.")
                
                temp_data = db.get_temp_data(user_id) or "style:anime"
                style = temp_data.replace("style:", "")
                
                try:
                    # 1. Скачиваем оригинал
                    original_bytes = max_api.download_image_from_max(incoming_image_token)
                    if not original_bytes:
                        raise Exception("Не удалось скачать фото из MAX")
                    
                    # 2. Обрабатываем в Hugging Face
                    processed_bytes = huggingface_client.generate_avatar(original_bytes, style)
                    
                    # 3. Загружаем результат обратно в MAX
                    new_token = max_api.upload_image_to_max(processed_bytes, f"avatar_{user_id}.jpg")
                    
                    if new_token:
                        max_api.send_image_message(
                            chat_id, 
                            f"✨ Готово! Твоя аватарка в стиле **{style.capitalize()}**.\n\nХочешь попробовать другой стиль? Выбери его в главном меню!", 
                            new_token
                        )
                    else:
                        raise Exception("Не удалось загрузить результат в MAX")
                        
                    db.set_user_state(user_id, 'idle')
                    db.save_temp_data(user_id, "")
                    
                except Exception as e:
                    logger.error(f"Ошибка генерации аватара: {e}")
                    max_api.send_message(chat_id, f"❌ Упс, что-то пошло не так: {str(e)}\n\nПопробуй отправить фото еще раз или выбери другой стиль.", attachments=keyboards.get_back_keyboard())
                    db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Пожалуйста, отправь именно фотографию (нажми на скрепку 📎), а не текст.", attachments=keyboards.get_back_keyboard())
        
        # --- СОСТОЯНИЕ ПО УМОЛЧАНИЮ ---
        else:
            max_api.send_message(chat_id, messages.UNKNOWN_COMMAND, attachments=keyboards.get_main_keyboard())
        
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ Исключение в handle_message: {e}", exc_info=True)
        return jsonify({"ok": True}), 200
