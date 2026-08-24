"""
Обработчики текстовых сообщений и фото
"""
import logging
import json
import requests
from flask import jsonify

import database as db
from app.utils import max_api
from app.utils import gigachat_image_client
from app import keyboards
from app import messages

logger = logging.getLogger("bot")


def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        
        message_id = message.get('id') or message.get('message_id') or data.get('update_id')
        if message_id:
            if db.is_message_processed(message_id):
                return jsonify({"ok": True}), 200
            db.mark_message_processed(message_id)
        
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
        
        if text.lower() == "/start":
            db.set_user_state(user_id, 'idle')
            max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_keyboard())
            return jsonify({"ok": True}), 200
        
        # --- СЦЕНАРИЙ: ОПИСАНИЕ ДЛЯ AI ПОРТРЕТА ---
        if state == 'avatar_describing':
            db.save_temp_data(user_id, text) # Сохраняем описание
            db.set_user_state(user_id, 'avatar_choosing_style')
            max_api.send_message(
                chat_id, 
                f"Отлично, я запомнил: *{text}*\n\nТеперь выбери стиль для своего портрета:", 
                attachments=keyboards.get_avatar_styles_keyboard()
            )

        # --- СЦЕНАРИЙ: ГЕНЕРАЦИЯ КАРТИНОК ПО ТЕКСТУ ---
        elif state == 'waiting_image_prompt':
            if text:
                max_api.send_message(chat_id, "🎨 Кандинский рисует... Это займет 15-30 секунд.")
                try:
                    processed_bytes = gigachat_image_client.generate_image(prompt=text)
                    new_token = gigachat_image_client.upload_to_max_api(processed_bytes)
                    if new_token:
                        max_api.send_image_message(chat_id, f"✨ Готово! Шедевр по твоему запросу:\n\n*{text}*", new_token)
                    else:
                        raise Exception("Не удалось загрузить результат в MAX API")
                    db.set_user_state(user_id, 'idle')
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации картинки: {e}")
                    max_api.send_message(chat_id, f"❌ Упс, ошибка: {str(e)}\n\n💡 *Совет:* Если модель 'просыпается', подожди 30 сек и отправь запрос еще раз!", attachments=keyboards.get_back_keyboard())
                    db.set_user_state(user_id, 'idle')

        # --- СЦЕНАРИЙ: ГЕНЕРАТОР МЕМОВ ---
        elif state == 'waiting_meme_text':
            if text:
                max_api.send_message(chat_id, "🎨 Леплю мем... Секунду!")
                try:
                    # Используем простой локальный генератор или API, если он подключен. 
                    # Для стабильности пока вернем заглушку или используем тот же gigachat, но с промптом "сделай мем"
                    # Но лучше использовать тот код мема, который мы писали ранее. 
                    # Для краткости здесь оставим генерацию через GigaChat с промптом "сделай мем с текстом"
                    prompt = f"Создай смешной мем на тему: {text}. На картинке должен быть крупный, читаемый текст."
                    processed_bytes = gigachat_image_client.generate_image(prompt=prompt)
                    new_token = gigachat_image_client.upload_to_max_api(processed_bytes)
                    if new_token:
                        max_api.send_image_message(chat_id, "Держи свой мем! 😂", new_token)
                    db.set_user_state(user_id, 'idle')
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации мема: {e}")
                    max_api.send_message(chat_id, f"❌ Ошибка: {str(e)}", attachments=keyboards.get_back_keyboard())
                    db.set_user_state(user_id, 'idle')

        # --- СЦЕНАРИЙ: AI ТЕКСТЫ ---
        elif state == 'waiting_text_prompt':
            if text:
                max_api.send_message(chat_id, "📝 Пишу текст... Секунду.")
                try:
                    # Используем GigaChat для генерации текста (без function_call)
                    token = gigachat_image_client.get_gigachat_token()
                    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                    payload = {
                        "model": "GigaChat-Pro",
                        "messages": [{"role": "user", "content": f"Напиши качественный текст на тему: {text}"}]
                    }
                    resp = requests.post(gigachat_image_client.API_URL, headers=headers, json=payload, timeout=30, verify=False)
                    resp.raise_for_status()
                    result_text = resp.json()["choices"][0]["message"]["content"]
                    max_api.send_message(chat_id, f"✨ Готово:\n\n{result_text}", attachments=keyboards.get_back_keyboard())
                    db.set_user_state(user_id, 'idle')
                except Exception as e:
                    logger.error(f"❌ Ошибка генерации текста: {e}")
                    max_api.send_message(chat_id, f"❌ Ошибка: {str(e)}", attachments=keyboards.get_back_keyboard())
                    db.set_user_state(user_id, 'idle')

        # --- СОСТОЯНИЕ ПО УМОЛЧАНИЮ ---
        else:
            max_api.send_message(chat_id, messages.UNKNOWN_COMMAND, attachments=keyboards.get_main_keyboard())
        
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКОЕ ИСКЛЮЧЕНИЕ в handle_message: {e}", exc_info=True)
        return jsonify({"ok": True}), 200
