"""
Обработчики текстовых сообщений и фото для развлекательной экосистемы
"""
import logging
from flask import jsonify

import database as db
from app.utils import max_api
# Здесь позже подключим AI-клиенты:
# from app.utils import huggingface_client, gigachat_client 
from app import keyboards
from app import messages

logger = logging.getLogger("bot")


def handle_message(data, chat_id, user_id, first_name):
    try:
        message = data.get('message', {})
        
        # 1. Защита от дублей (из твоего оригинального кода)
        message_id = message.get('id') or message.get('message_id') or data.get('update_id')
        if message_id:
            if db.is_message_processed(message_id):
                logger.info(f"🔁 Дубликат сообщения {message_id} — пропускаем")
                return jsonify({"ok": True}), 200
            db.mark_message_processed(message_id)
        
        # 2. Извлечение текста и картинки
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
        logger.info(f"📩 Текст: '{text[:30]}...' | Фото: {bool(incoming_image_token)} | State: '{state}' | user_id={user_id}")
        
        if user_id and chat_id:
            db.save_chat_id(user_id, chat_id)
        
        # 3. Глобальная команда /start
        if text.lower() == "/start":
            db.set_user_state(user_id, 'idle')
            max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_menu_keyboard())
            return jsonify({"ok": True}), 200
        
        # 4. Машина состояний (FSM)
        
        # --- СЦЕНАРИЙ: AI АВАТАРКИ (Ждем фото) ---
        if state == 'avatar_waiting_photo':
            if incoming_image_token:
                max_api.send_message(chat_id, "🎨 Получил фото! Превращаю в шедевр... Это займет 15-30 секунд.")
                # TODO: Здесь будет вызов huggingface_client.process_avatar(incoming_image_token, style)
                # Временная заглушка для теста:
                max_api.send_message(chat_id, "✅ [Тест] Аватарка успешно сгенерирована! (Здесь будет реальная картинка)", attachments=keyboards.get_main_menu_keyboard())
                db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Пожалуйста, отправь именно фотографию (нажми на скрепку 📎), а не текст.", attachments=keyboards.get_back_keyboard())

        # --- СЦЕНАРИЙ: ГЕНЕРАЦИЯ КАРТИНОК (Ждем текст) ---
        elif state == 'image_waiting_prompt':
            if text:
                max_api.send_message(chat_id, "🖼️ Рисую... Подожди немного 🎨")
                # TODO: Здесь будет вызов image_client.generate_image(text, user_id)
                max_api.send_message(chat_id, f"✅ [Тест] Картинка по запросу '{text}' готова!", attachments=keyboards.get_main_menu_keyboard())
                db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Напиши описание картинки текстом.", attachments=keyboards.get_back_keyboard())

        # --- СЦЕНАРИЙ: МЕМЫ (Ждем фото) ---
        elif state == 'meme_waiting_photo':
            if incoming_image_token:
                max_api.send_message(chat_id, "😂 Загружаю фото в мем-генератор...")
                # TODO: Вызов gigachat для придумывания подписей + наложение на фото
                max_api.send_message(chat_id, "✅ [Тест] Мем готов! Смотри, как смешно!", attachments=keyboards.get_main_menu_keyboard())
                db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Для создания мема нужно фото. Отправь картинку!", attachments=keyboards.get_back_keyboard())

        # --- СЦЕНАРИЙ: ГОРОСКОП/ТАРО (Ждем текст: знак зодиака или вопрос) ---
        elif state in ['horoscope_choosing', 'horoscope_waiting_input']:
            if text:
                max_api.send_message(chat_id, "🔮 Считываю энергии и составляю прогноз...")
                # TODO: Вызов gigachat_client.generate_horoscope(text, mode)
                max_api.send_message(chat_id, f"✅ [Тест] Твой персональный прогноз для запроса '{text}' готов!", attachments=keyboards.get_main_menu_keyboard())
                db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Напиши свой знак зодиака или вопрос.", attachments=keyboards.get_back_keyboard())

        # --- СЦЕНАРИЙ: AI СОБЕСЕДНИК (Ждем текст) ---
        elif state == 'chat_active':
            if text:
                character = db.get_temp_data(user_id).replace("character:", "")
                max_api.send_message(chat_id, "⏳ Думаю над ответом...")
                # TODO: Вызов gigachat_client.chat_with_character(text, character)
                max_api.send_message(chat_id, f"✅ [Тест] Ответ от персонажа '{character}' на твой текст: '{text}'", attachments=keyboards.get_back_keyboard())
            else:
                max_api.send_message(chat_id, "⚠️ Напиши сообщение, чтобы продолжить диалог.")

        # --- СЦЕНАРИЙ: AI КОНТЕНТ (Ждем текст) ---
        elif state == 'content_waiting_topic':
            if text:
                max_api.send_message(chat_id, "📝 Анализирую тренды и пишу контент...")
                # TODO: Вызов gigachat_client.generate_social_post(text)
                max_api.send_message(chat_id, f"✅ [Тест] Пост на тему '{text}' готов!", attachments=keyboards.get_main_menu_keyboard())
                db.set_user_state(user_id, 'idle')
            else:
                max_api.send_message(chat_id, "⚠️ Напиши тему для поста.", attachments=keyboards.get_back_keyboard())

        # --- СОСТОЯНИЕ ПО УМОЛЧАНИЮ (IDLE) ---
        elif state == 'idle':
            if text:
                # Если пользователь просто пишет текст в главном меню, предлагаем выбрать функцию
                max_api.send_message(chat_id, "👋 Я пока не понимаю эту команду. Выбери действие в меню ниже!", attachments=keyboards.get_main_menu_keyboard())
        
        else:
            # Сброс неизвестного состояния
            db.set_user_state(user_id, 'idle')
            max_api.send_message(chat_id, "Произошла ошибка состояния. Вернитесь в главное меню.", attachments=keyboards.get_main_menu_keyboard())
        
        return jsonify({"ok": True}), 200
    
    except Exception as e:
        logger.error(f"❌ Исключение в handle_message: {e}", exc_info=True)
        # Даже при критической ошибке возвращаем 200, чтобы MAX не спамил вебхуками
        return jsonify({"ok": True}), 200
