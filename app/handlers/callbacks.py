"""
Обработчики нажатий на кнопки (callback)
"""
import logging
from flask import jsonify

import database as db
from app.utils import max_api
from app import keyboards

logger = logging.getLogger("bot")


def handle_callback(data, chat_id, user_id, first_name, callback_id):
    logger.info(f"🔘 Кнопка '{data}' | user_id={user_id} | chat_id={chat_id}")
    
    if not (callback_id and chat_id and user_id):
        return jsonify({"ok": True}), 200
    
    db.save_chat_id(user_id, chat_id)
    
    # --- ГЛАВНОЕ МЕНЮ ---
    if data == "main_menu":
        db.set_user_state(user_id, 'idle')
        max_api.answer_callback(callback_id, "Возвращаемся в меню")
        max_api.send_message(chat_id, "🏠 Главное меню:", attachments=keyboards.get_main_keyboard())
    
    # --- AI АВАТАРКИ ---
    elif data == "ai_avatars":
        db.set_user_state(user_id, 'avatar_choosing_style')
        max_api.answer_callback(callback_id, "Открываю студию...")
        max_api.send_message(chat_id, "🎨 Выбери стиль для своей аватарки:", attachments=keyboards.get_avatar_styles_keyboard())
    
    elif data.startswith("style_"):
        style = data.replace("style_", "")
        db.save_temp_data(user_id, f"style:{style}")
        db.set_user_state(user_id, 'avatar_waiting_photo')
        max_api.answer_callback(callback_id, "Стиль выбран!")
        max_api.send_message(
            chat_id, 
            f"📸 Отлично! Теперь отправь мне свое фото, и я превращу его в стиль **{style.capitalize()}**.\n\n💡 *Совет: чем четче фото, тем лучше результат.*", 
            attachments=keyboards.get_back_keyboard()
        )
        
    # --- ГЕНЕРАЦИЯ КАРТИНОК ПО ТЕКСТУ ---
    elif data == "generate_image":
        db.set_user_state(user_id, 'waiting_image_prompt')
        max_api.answer_callback(callback_id, "Готов к творчеству!")
        max_api.send_message(
            chat_id, 
            "🖼️ Опиши словами, что ты хочешь увидеть.\n\n*Например:* 'Кот в скафандре на Луне, фотореалистично'", 
            attachments=keyboards.get_back_keyboard()
        )
    
    # --- ГЕНЕРАТОР МЕМОВ ---
    elif data == "meme_generator":
        db.set_user_state(user_id, 'waiting_meme_text')
        max_api.answer_callback(callback_id, "Режим мемолога активирован!")
        max_api.send_message(
            chat_id, 
            "😂 Отправь текст для мема!\n\n"
            "💡 *Формат:* `Текст сверху / Текст снизу`\n"
            "*(Используй слэш `/` или тире `-` как разделитель)*\n\n"
            "Пример: `Когда написал код / И он заработал с первого раза`\n"
            "Если не ставить разделитель, я сам красиво разобью текст 😉", 
            attachments=keyboards.get_back_keyboard()
        )
    
    # --- AI ГОРОСКОП (заглушка) ---
    elif data == "ai_horoscope":
        max_api.answer_callback(callback_id, "Функция в разработке 🛠️")
        max_api.send_message(chat_id, "🔮 AI Гороскоп скоро будет доступен! Следите за обновлениями.", attachments=keyboards.get_back_keyboard())
    
    else:
        max_api.answer_callback(callback_id, "Функция в разработке 🛠️")
    
    return jsonify({"ok": True}), 200
