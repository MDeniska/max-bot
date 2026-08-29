# -*- coding: utf-8 -*-

def get_main_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🖼️ Картинки (Sber)", "payload": "gen_sber"}, 
                 {"type": "callback", "text": "💬 AI Чат", "payload": "ai_chat"}],
                [{"type": "callback", "text": "👑 VIP Генерация", "payload": "vip_gen_menu"}, 
                 {"type": "callback", "text": "🎭 VIP Аватарки", "payload": "vip_avatar_menu"}],
                [{"type": "callback", "text": "🛠️ Фото-инструменты", "payload": "vip_tools_menu"}, 
                 {"type": "callback", "text": "💰 Мой баланс", "payload": "show_balance"}]
            ]
        }
    }]

def get_vip_gen_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🌟 VIP Картинка", "payload": "vip_text2img"}, 
                 {"type": "callback", "text": "🎨 VIP Фото", "payload": "vip_img2img"}],
                [{"type": "callback", "text": "🖼️ Коллаж (2-8 фото)", "payload": "vip_collage"}, 
                 {"type": "callback", "text": "👗 Сменить одежду", "payload": "vip_tryon"}],
                [{"type": "callback", "text": "🏠 Назад", "payload": "main_menu"}]
            ]
        }
    }]

def get_vip_tools_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🧹 Удалить объект", "payload": "vip_eraser"}, 
                 {"type": "callback", "text": "🔍 Улучшить фото", "payload": "vip_upscale"}],
                [{"type": "callback", "text": "🏠 Дизайн интерьера", "payload": "vip_interior"}, 
                 {"type": "callback", "text": "🏠 Назад", "payload": "main_menu"}]
            ]
        }
    }]

def get_vip_avatar_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🎭 Аниме / Скетч", "payload": "vip_style_anime"}, 
                 {"type": "callback", "text": "🦁 В стиле животного", "payload": "vip_style_animal"}],
                [{"type": "callback", "text": "👴 Состарить / Омолодить", "payload": "vip_style_age"}, 
                 {"type": "callback", "text": "🎬 Со знаменитостью", "payload": "vip_style_celeb"}],
                [{"type": "callback", "text": "🏠 Назад", "payload": "main_menu"}]
            ]
        }
    }]

def get_balance_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "💳 Пополнить", "payload": "top_up_balance"}, 
                 {"type": "callback", "text": "📜 Тарифы", "payload": "vip_tariffs"}],
                [{"type": "callback", "text": "🏠 Назад", "payload": "main_menu"}]
            ]
        }
    }]

def get_back_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [[{"type": "callback", "text": "🏠 Главное меню", "payload": "main_menu"}]]
        }
    }]
