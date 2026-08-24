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
    
    if data == "main_menu":
        db.set_user_state(user_id, 'idle')
        max_api.answer_callback(callback_id, "Возвращаемся в меню")
        max_api.send_message(chat_id, "🏠 Главное меню. Выберите функцию:", attachments=keyboards.get_main_keyboard())
        
    elif data == "ai_avatars":
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
        db.save_temp_data(user_id, f"style:{style}")
        db.set_user_state(user_id, 'avatar_generating')
        max_api.answer_callback(callback_id, "Стиль выбран! Рисую...")
        max_api.send_message(chat_id, f"🎨 Отлично! Создаю портрет. Это займет 15-30 секунд...")
        # Логика генерации сработает в messages.py при следующем шаге, но мы можем вызвать её сразу, 
        # однако для простоты потоков, мы попросим пользователя подтвердить или сгенерируем заглушку.
        # Лучший вариант: сразу генерируем, если описание уже есть.
        desc = db.get_temp_data(user_id).replace(f"style:{style}", "").strip()
        if not desc or desc == f"style:{style}":
             desc = "портрет человека"
             
        max_api.send_message(chat_id, f"✨ Готово! (Демонстрация: портрет '{desc}' в стиле {style} будет реализован через GigaChat)", attachments=keyboards.get_back_keyboard())
        db.set_user_state(user_id, 'idle')

    elif data == "generate_image":
        db.set_user_state(user_id, 'waiting_image_prompt')
        max_api.answer_callback(callback_id, "Готов к творчеству!")
        max_api.send_message(
            chat_id, 
            "🖼️ Опиши словами, что ты хочешь увидеть.\n\n*Например:* 'Кот в скафандре на Луне, фотореалистично'", 
            attachments=keyboards.get_back_keyboard()
        )
        
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

    elif data == "ai_chat":
        db.set_user_state(user_id, 'waiting_chat_prompt')
        max_api.answer_callback(callback_id, "Включаю режим собеседника")
        max_api.send_message(
            chat_id, 
            "💬 Я готов к общению! Напиши мне любое сообщение или вопрос, и я отвечу.", 
            attachments=keyboards.get_back_keyboard()
        )
        
    elif data == "ai_content":
        db.set_user_state(user_id, 'waiting_content_prompt')
        max_api.answer_callback(callback_id, "Включаю режим копирайтера")
        max_api.send_message(
            chat_id, 
            "📝 Напиши тему или задачу для текста.\n\n*Например:* 'Напиши короткий пост о пользе нейросетей для бизнеса'", 
            attachments=keyboards.get_back_keyboard()
        )
        
    elif data == "about_bot":
        max_api.answer_callback(callback_id, "Информация о боте")
        max_api.send_message(
            chat_id, 
            "🤖 **О боте**\n\n"
            "Этот бот использует передовые российские нейросети (GigaChat / Кандинский) для:\n"
            "• Генерации картинок и аватарок по тексту\n"
            "• Создания мемов\n"
            "• Написания текстов и общения\n\n"
            "Версия: 1.0.0", 
            attachments=keyboards.get_back_keyboard()
        )
        
    else:
        max_api.answer_callback(callback_id, "Функция в разработке 🛠️")
    
    return jsonify({"ok": True}), 200
