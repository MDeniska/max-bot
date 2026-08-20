"""
Все клавиатуры бота в одном месте
"""

def get_main_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🎨 AI Аватарки", "payload": "ai_avatars"}],
                [{"type": "callback", "text": "🖼️ Генерация картинок", "payload": "generate_image"}],
                [{"type": "callback", "text": "😂 Генератор мемов", "payload": "meme_generator"}],
                [{"type": "callback", "text": "🔮 AI Гороскоп", "payload": "ai_horoscope"}],
                [{"type": "callback", "text": "🤖 AI Собеседник", "payload": "ai_chat"}],
                [{"type": "callback", "text": "📝 AI Контент", "payload": "ai_content"}]
            ]
        }
    }]


def get_back_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🏠 Главное меню", "payload": "main_menu"}]
            ]
        }
    }]


def get_avatar_styles_keyboard():
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🎭 Аниме", "payload": "style_anime"}],
                [{"type": "callback", "text": "🌌 Киберпанк", "payload": "style_cyberpunk"}],
                [{"type": "callback", "text": "🎨 Масло", "payload": "style_oil"}],
                [{"type": "callback", "text": "💧 Акварель", "payload": "style_watercolor"}]
            ]
        }
    }]
