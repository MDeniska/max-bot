"""
Обработчики текстовых сообщений и фото
"""
import logging
import json
import requests
from flask import jsonify

import database as db
from app.utils import max_api
from app.utils import huggingface_client   # Для аватарок (сохранение лица)
from app.utils import kandinsky_client  # Для генерации по тексту
from app.utils import meme_generator       # Для мемов
from app import keyboards
from app import messages

logger = logging.getLogger("bot")


def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        
        # 1. Защита от дубликатов сообщений
        message_id = message.get('id') or message.get('message_id') or data.get('update_id')
        if message_id:
            if db.is_message_processed(message_id):
                logger.info(f"🔁 Дубликат сообщения {message_id} — пропускаем")
                return jsonify({"ok": True}), 200
            db.mark_message_processed(message_id)
        
        # 2. Извлечение текста и вложений
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
        
        # 3. Получение текущего состояния пользователя
        state = db.get_user_state(user_id)
        logger.info(f"📩 Текст: '{text[:20]}...' | Фото: {bool(incoming_image_url)} | State: '{state}' | user_id={user_id}")
        
        if user_id and chat_id:
            db.save_chat_id(user_id, chat_id)
        
        # 4. Глобальная команда /start
        if text.lower() == "/start":
            db.set_user_state(user_id, 'idle')
            max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_keyboard())
            return jsonify({"ok": True}), 200
        
        # 5. СЦЕНАРИЙ: AI АВАТАРКИ (Ожидаем фото) -> ИСПОЛЬЗУЕМ HUGGING FACE
        if state == 'avatar_waiting_photo':
            if incoming_image_url:
                max_api.send_message(chat_id, "🎨 Получил фото! Магия начинается... Это займет 15-30 секунд.")
                
                temp_data = db.get_temp_data(user_id) or "style:anime"
                style_key = temp_data.replace("style:", "")
                
                try:
                    # Шаг А: Скачиваем исходное фото
                    logger.info(f"📥 Скачиваем исходное фото: {incoming_image_url}")
                    resp = requests.get(incoming_image_url, timeout=15)
                    resp.raise_for_status()
                    original_bytes = resp.content
                    
                    # Шаг Б: Отправляем в Hugging Face для стилизации с сохранением лица
                    logger.info(f"🎨 Отправляем в Hugging Face (стиль: {style_key})...")
                    processed_bytes = huggingface_client.generate_avatar(original_bytes, style_key)
                    
                    # Шаг В: Загружаем результат обратно в MAX API
                    logger.info("📤 Загружаем результат в MAX API...")
                    new_token = max_api.upload_image_to_max(processed_bytes, f"avatar_{user_id}.jpg")
                    
                    if new_token:
                        max_api.send_image_message(
                            chat_id, 
                            f"✨ Готово! Твоя аватарка в стиле **{style_key.capitalize()}**.\n\nХочешь попробовать другой стиль? Нажми 'Главное меню'!", 
                            new_token
                        )
                    else:
                        raise Exception("Не удалось загрузить результат в MAX API (пустой токен)")
                        
                    # Шаг Г: Сбрасываем состояние
                    db.set_user_state(user_id, 'idle')
                    db.save_temp_data(user_id, "")
                    logger.info("✅ Сценарий аватарки успешно завершен")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации аватара: {e}")
                    max_api.send_message(
                        chat_id, 
                        f"❌ Упс, произошла ошибка: {str(e)}\n\n💡 *Совет:* Если модель 'проснулась', просто отправь фото еще раз!", 
                        attachments=keyboards.get_back_keyboard()
                    )
                    db.set_user_state(user_id, 'idle')
            else:
                # Пользователь отправил текст вместо фото
                max_api.send_message(chat_id, "⚠️ Пожалуйста, отправь именно фотографию (нажми на скрепку 📎 или значок картинки).", attachments=keyboards.get_back_keyboard())
        
        # 6. СЦЕНАРИЙ: ГЕНЕРАЦИЯ КАРТИНОК ПО ТЕКСТУ -> ИСПОЛЬЗУЕМ STABLE HORDE
        elif state == 'waiting_image_prompt':
            if text:
                max_api.send_message(chat_id, "🎨 Магия начинается... Рисую по твоему описанию. Это займет 20-40 секунд.")
                
                try:
                    # Генерируем картинку по тексту (512x512 для скорости и бесплатных лимитов)
                    processed_bytes = stable_horde_client.generate_image_from_text(
                        prompt=text,
                        width=512,
                        height=512
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
        
        # 7. СЦЕНАРИЙ: ГЕНЕРАТОР МЕМОВ -> ИСПОЛЬЗУЕМ MEME_GENERATOR
        elif state == 'waiting_meme_text':
            if text:
                max_api.send_message(chat_id, "🎨 Леплю мем... Секунду!")
                
                try:
                    # 1. Генерируем мем
                    meme_bytes = meme_generator.generate_meme(text)
                    
                    # 2. Загружаем в MAX
                    new_token = meme_generator.upload_to_max_api(meme_bytes)
                    
                    if new_token:
                        max_api.send_image_message(
                            chat_id, 
                            "Держи свой мем! 😂\n\nХочешь еще? Отправь новый текст или жми 'Главное меню'.", 
                            new_token
                        )
                    else:
                        raise Exception("Не удалось загрузить мем в MAX API")
                        
                    # Возвращаем в главное меню после отправки
                    db.set_user_state(user_id, 'idle')
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации мема: {e}")
                    max_api.send_message(
                        chat_id, 
                        f"❌ Упс, ошибка: {str(e)}\n\nПопробуй написать текст короче или используй формат 'Текст | Текст'.", 
                        attachments=keyboards.get_back_keyboard()
                    )
                    db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Пожалуйста, напиши текст для мема.", attachments=keyboards.get_back_keyboard())
        
        # 8. СОСТОЯНИЕ ПО УМОЛЧАНИЮ (если пользователь пишет что-то вне сценария)
        else:
            max_api.send_message(chat_id, messages.UNKNOWN_COMMAND, attachments=keyboards.get_main_keyboard())
        
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКОЕ ИСКЛЮЧЕНИЕ в handle_message: {e}", exc_info=True)
        # Всегда возвращаем 200, чтобы MAX не спамил вебхуками при ошибке
        return jsonify({"ok": True}), 200
