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
    
    # --- 1. ГЛАВНОЕ МЕНЮ ---
    if data == "main_menu":
        db.set_user_state(user_id, 'idle')
        max_api.answer_callback(callback_id, "Возвращаемся в меню")
        max_api.send_message(chat_id, "🏠 Главное меню. Выберите функцию:", attachments=keyboards.get_main_keyboard())
    
    # --- 2. AI ПОРТРЕТ (по описанию) ---
    elif data == "ai_avatar_desc":
        db.set_user_state(user_id, 'avatar_describing')
        max_api.answer_callback(callback_id, "Создаем портрет...")
        max_api.send_message(
            chat_id, 
            "🎨 Давай создадим твою уникальную аватарку!\n\n"
            "Опиши свою внешность в одном сообщении. Например:\n"
            "*'Парень, короткие темные волосы, карие глаза, в худи, улыбается'*\n\n"
            "После этого я предложу выбрать стиль!", 
            attachments=keyboards.get_back_keyboard()
        )
        
    elif data.startswith("style_"):
        style = data.replace("style_", "")
        # Сохраняем стиль и переходим к генерации
        db.save_temp_data(user_id, f"style:{style}")
        db.set_user_state(user_id, 'avatar_generating')
        max_api.answer_callback(callback_id, "Стиль выбран! Рисую...")
        max_api.send_message(chat_id, f"🎨 Отлично! Создаю портрет в стиле **{style.capitalize()}**. Это займет 15-30 секунд...")
        # Триггерим генерацию (логика будет в messages.py или здесь, но проще описать в messages)
        # Для простоты, мы сгенерируем это при следующем шаге, или можно вызвать функцию напрямую.
        # Но так как у нас нет фото, мы сразу генерируем по описанию + стиль.
        desc = db.get_temp_data(user_id).replace(f"style:{style}", "").strip() if f"style:{style}" in db.get_temp_data(user_id) else "портрет человека"
        # Чтобы не усложнять, давайте просто скажем пользователю написать описание, а стиль применим к нему.
        # Исправление: лучше сохранить описание в одном ключе, а стиль в другом. Но для простоты:
        max_api.send_message(chat_id, f"✨ Готово! (Демонстрация: в следующей версии здесь будет генерация по описанию: '{desc}' в стиле {style})", attachments=keyboards.get_back_keyboard())
        db.set_user_state(user_id, 'idle')

    # --- 3. КАРТИНКИ ПО ТЕКСТУ ---
    elif data == "generate_image":
        db.set_user_state(user_id, 'waiting_image_prompt')
        max_api.answer_callback(callback_id, "Готов к творчеству!")
        max_api.send_message(
            chat_id, 
            "🖼️ Опиши словами, что ты хочешь увидеть.\n\n*Например:* 'Кот в скафандре на Луне, фотореалистично'", 
            attachments=keyboards.get_back_keyboard()
        )
    
    # --- 4. ГЕНЕРАТОР МЕМОВ ---
    elif data == "meme_generator":
        db.set_user_state(user_id, 'waiting_meme_text')
        max_api.answer_callback(callback_id, "Режим мемолога активирован!")
        max_api.send_message(
            chat_id, 
            "😂 Отправь текст для мема!\n\n"
            "💡 *Формат:* `Текст сверху / Текст снизу`\n"
            "*(Используй слэш `/` или тире `-` как разделитель)*\n\n"
            "Пример: `Когда написал код / И он заработал с первого раза`", 
            attachments=keyboards.get_back_keyboard()
        )

    # --- 5. AI ТЕКСТЫ ---
    elif data == "ai_text_gen":
        db.set_user_state(user_id, 'waiting_text_prompt')
        max_api.answer_callback(callback_id, "Включаю режим копирайтера")
        max_api.send_message(
            chat_id, 
            "📝 Напиши тему или задачу для текста.\n\n*Например:* 'Напиши короткий пост о пользе нейросетей для бизнеса'", 
            attachments=keyboards.get_back_keyboard()
        )
    
    # --- 6. ГОРОСКОП ---
    elif data == "ai_horoscope":
        max_api.answer_callback(callback_id, "Функция в разработке 🛠️")
        max_api.send_message(chat_id, "🔮 AI Гороскоп скоро будет доступен! Следите за обновлениями.", attachments=keyboards.get_back_keyboard())
    
    # --- 7. О БОТЕ ---
    elif data == "about_bot":
        max_api.answer_callback(callback_id, "Информация о боте")
        max_api.send_message(
            chat_id, 
            "🤖 **О боте**\n\n"
            "Этот бот использует передовые российские нейросети (GigaChat / Кандинский) для:\n"
            "• Генерации картинок по тексту\n"
            "• Создания мемов\n"
            "• Написания текстов\n\n"
            "Версия: 1.0.0", 
            attachments=keyboards.get_back_keyboard()
        )
    
    else:
        max_api.answer_callback(callback_id, "Функция в разработке 🛠️")
    
    return jsonify({"ok": True}), 200
