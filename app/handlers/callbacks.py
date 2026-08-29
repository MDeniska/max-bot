# -*- coding: utf-8 -*-
import logging
from flask import jsonify
import database as db
from app.utils import max_api
from app import keyboards

logger = logging.getLogger("bot")

def handle_callback(data, chat_id, user_id, first_name, callback_id):
    logger.info(f"Button '{data}' | user_id={user_id} | chat_id={chat_id}")
    if not (callback_id and chat_id and user_id):
        return jsonify({"ok": True}), 200
    db.save_chat_id(user_id, chat_id)

    if data == "main_menu":
        db.set_user_state(user_id, 'idle')
        max_api.answer_callback(callback_id, "Menu")
        max_api.send_message(chat_id, "🏠 Главное меню", attachments=keyboards.get_main_keyboard())
        
    elif data == "gen_sber":
        db.set_user_state(user_id, 'waiting_image_prompt')
        max_api.answer_callback(callback_id, "Sber")
        max_api.send_message(chat_id, "🖼️ Напиши описание картинки:", attachments=keyboards.get_back_keyboard())
        
    elif data == "ai_chat":
        db.set_user_state(user_id, 'waiting_chat_prompt')
        max_api.answer_callback(callback_id, "Chat")
        max_api.send_message(chat_id, "💬 Напиши любое сообщение:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_gen_menu":
        max_api.answer_callback(callback_id, "VIP Gen")
        max_api.send_message(chat_id, "👑 Выбери инструмент VIP генерации:", attachments=keyboards.get_vip_gen_keyboard())
        
    elif data == "vip_tools_menu":
        max_api.answer_callback(callback_id, "Tools")
        max_api.send_message(chat_id, "🛠️ Выбери фото-инструмент:", attachments=keyboards.get_vip_tools_keyboard())
        
    elif data == "vip_avatar_menu":
        max_api.answer_callback(callback_id, "Avatars")
        max_api.send_message(chat_id, "🎭 Выбери стиль аватарки:", attachments=keyboards.get_vip_avatar_keyboard())
        
    elif data == "show_balance":
        max_api.answer_callback(callback_id, "Balance")
        max_api.send_message(chat_id, "💰 Баланс: 0.0 USDT", attachments=keyboards.get_balance_keyboard())
        
    elif data == "vip_text2img":
        db.set_user_state(user_id, 'waiting_vip_text_prompt')
        max_api.answer_callback(callback_id, "VIP Text")
        max_api.send_message(chat_id, "🌟 Напиши описание для VIP картинки:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_img2img":
        db.set_user_state(user_id, 'waiting_vip_img2img_photo')
        max_api.answer_callback(callback_id, "VIP Photo")
        max_api.send_message(chat_id, "🎨 Отправь фото для стилизации:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_collage":
        db.set_user_state(user_id, 'waiting_collage_photos')
        db.save_temp_data(user_id, 'collage:0')
        max_api.answer_callback(callback_id, "Collage")
        max_api.send_message(chat_id, "🖼️ Отправь от 2 до 8 фото для коллажа:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_tryon":
        db.set_user_state(user_id, 'waiting_tryon_photo')
        max_api.answer_callback(callback_id, "Tryon")
        max_api.send_message(chat_id, "👗 Отправь фото человека:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_eraser":
        db.set_user_state(user_id, 'waiting_eraser_photo')
        max_api.answer_callback(callback_id, "Eraser")
        max_api.send_message(chat_id, "🧹 Отправь фото и укажи, что удалить:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_upscale":
        db.set_user_state(user_id, 'waiting_upscale_photo')
        max_api.answer_callback(callback_id, "Upscale")
        max_api.send_message(chat_id, "🔍 Отправь размытое фото для улучшения:", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_interior":
        db.set_user_state(user_id, 'waiting_interior_photo')
        max_api.answer_callback(callback_id, "Interior")
        max_api.send_message(chat_id, "🏠 Отправь фото комнаты:", attachments=keyboards.get_back_keyboard())
        
    elif data.startswith("vip_style_"):
        style = data.replace("vip_style_", "")
        db.save_temp_data(user_id, f"avatar_style:{style}")
        db.set_user_state(user_id, 'waiting_avatar_photo')
        max_api.answer_callback(callback_id, "Style")
        max_api.send_message(chat_id, f"✅ Стиль '{style}' выбран. Отправь четкое фото лица:", attachments=keyboards.get_back_keyboard())
        
    elif data == "top_up_balance":
        max_api.answer_callback(callback_id, "Top up")
        max_api.send_message(chat_id, "💳 Пополнение баланса (в разработке)", attachments=keyboards.get_back_keyboard())
        
    elif data == "vip_tariffs":
        max_api.answer_callback(callback_id, "Tariffs")
        max_api.send_message(chat_id, "📜 Тарифы: VIP Картинка 0.1, Аватарка 0.5 USDT", attachments=keyboards.get_back_keyboard())
        
    else:
        max_api.answer_callback(callback_id, "Action")
        max_api.send_message(chat_id, "🏠 Главное меню", attachments=keyboards.get_main_keyboard())
    
    return jsonify({"ok": True}), 200
