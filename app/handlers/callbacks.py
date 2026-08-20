"""
Обработчики нажатий на кнопки (callback) для развлекательной экосистемы
"""
import logging
from flask import jsonify

import database as db
from app.utils import max_api
from app import keyboards
from app import messages

logger = logging.getLogger("bot")


def handle_callback(data, chat_id, user_id, first_name, callback_id):
    logger.info(f"🔘 Кнопка '{data}' | user_id={user_id} | chat_id={chat_id}")
    
    if not (callback_id and chat_id and user_id):
        return jsonify({"ok": True}), 200
    
    # Гарантируем, что пользователь есть в БД
    db.save_chat_id(user_id, chat_id)
    
    # ==========================================
    # НАВИГАЦИЯ И ГЛАВНОЕ МЕНЮ
    # ==========================================
    if data == "back_to_menu":
        db.set_user_state(user_id, 'idle')
        max_api.answer_callback(callback_id, "Возвращаемся в меню")
        max_api.send_message(chat_id, messages.WELCOME_MESSAGE, attachments=keyboards.get_main_menu_keyboard())
    
    # ==========================================
    # AI АВАТАРКИ
    # ==========================================
    elif data == "ai_avatars":
        db.set_user_state(user_id, 'avatar_waiting_photo')
        max_api.answer_callback(callback_id, "Открываю студию аватарок...")
        max_api.send_message(chat_id, messages.AI_AVATARS_MESSAGE, attachments=keyboards.get_avatar_styles_keyboard())
    
    elif data.startswith("style_"):
        # Пользователь выбрал стиль, теперь ждем фото
        style_name = data.replace("style_", "").capitalize()
        db.set_user_state(user_id, 'avatar_waiting_photo')
        # Сохраняем выбранный стиль во временные данные, чтобы использовать при генерации
        db.save_temp_data(user_id, f"style:{style_name}") 
        max_api.answer_callback(callback_id, f"Стиль '{style_name}' выбран!")
        max_api.send_message(chat_id, f"📸 Отлично! Теперь отправь мне свое фото, и я превращу его в стиль **{style_name}**.", attachments=keyboards.get_back_keyboard())

    # ==========================================
    # ГЕНЕРАЦИЯ КАРТИНОК (по тексту)
    # ==========================================
    elif data == "generate_image":
        db.set_user_state(user_id, 'image_waiting_prompt')
        max_api.answer_callback(callback_id, "Открываю генератор...")
        max_api.send_message(chat_id, messages.GENERATE_IMAGE_MESSAGE, attachments=keyboards.get_back_keyboard())

    # ==========================================
    # ГЕНЕРАТОР МЕМОВ
    # ==========================================
    elif data == "meme_generator":
        db.set_user_state(user_id, 'meme_waiting_photo')
        max_api.answer_callback(callback_id, "Запускаю мем-машину...")
        max_api.send_message(chat_id, messages.MEME_GENERATOR_MESSAGE, attachments=keyboards.get_back_keyboard())

    # ==========================================
    # AI ГОРОСКОП / ТАРО
    # ==========================================
    elif data == "ai_horoscope":
        db.set_user_state(user_id, 'horoscope_choosing')
        max_api.answer_callback(callback_id, "Открываю предсказания...")
        max_api.send_message(chat_id, messages.AI_HOROSCOPE_MESSAGE, attachments=keyboards.get_horoscope_types_keyboard())

    elif data in ["horoscope_daily", "tarot_spread", "numerology", "wish_map"]:
        db.save_temp_data(user_id, f"mode:{data}")
        db.set_user_state(user_id, 'horoscope_waiting_input')
        max_api.answer_callback(callback_id, "Принимаю запрос...")
        max_api.send_message(chat_id, "✨ Напиши свой знак зодиака, дату рождения или задай вопрос картам Таро:", attachments=keyboards.get_back_keyboard())

    # ==========================================
    # AI СОБЕСЕДНИК
    # ==========================================
    elif data == "ai_chat":
        db.set_user_state(user_id, 'chat_choosing')
        max_api.answer_callback(callback_id, "Загружаю персонажей...")
        max_api.send_message(chat_id, messages.AI_CHAT_MESSAGE, attachments=keyboards.get_chat_characters_keyboard())

    elif data.startswith("chat_"):
        character = data.replace("chat_", "")
        db.save_temp_data(user_id, f"character:{character}")
        db.set_user_state(user_id, 'chat_active')
        max_api.answer_callback(callback_id, "Персонаж выбран!")
        max_api.send_message(chat_id, f"💬 Привет! Я готов к общению. Напиши мне что-нибудь, и я отвечу в выбранном стиле.", attachments=keyboards.get_back_keyboard())

    # ==========================================
    # AI КОНТЕНТ И ИГРЫ
    # ==========================================
    elif data == "ai_content":
        db.set_user_state(user_id, 'content_waiting_topic')
        max_api.answer_callback(callback_id, "Открываю редактор...")
        max_api.send_message(chat_id, messages.AI_CONTENT_MESSAGE, attachments=keyboards.get_back_keyboard())

    elif data == "ai_games":
        max_api.answer_callback(callback_id, "Загружаю игры...")
        max_api.send_message(chat_id, messages.AI_GAMES_MESSAGE, attachments=keyboards.get_back_keyboard())

    # ==========================================
    # ПРЕМИУМ
    # ==========================================
    elif data == "premium":
        max_api.answer_callback(callback_id, "Открываю тарифы...")
        max_api.send_message(chat_id, messages.PREMIUM_MESSAGE, attachments=keyboards.get_back_keyboard())

    # ==========================================
    # ЗАГЛУШКА ДЛЯ НЕИЗВЕСТНЫХ КНОПОК
    # ==========================================
    else:
        max_api.answer_callback(callback_id, "Функция в разработке 🛠️")
    
    return jsonify({"ok": True}), 200
