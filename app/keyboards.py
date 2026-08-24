"""
Все клавиатуры бота. Строгая структура 2x3 для стабильного рендеринга в MAX.
"""

def get_main_keyboard():
    """Главное меню: строго 6 кнопок (2 колонки, 3 ряда)"""
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {"type": "callback", "text": "🎨 AI Портрет", "payload": "ai_avatar_desc"},
                    {"type": "callback", "text": "🖼️ Картинки по тексту", "payload": "generate_image"}
                ],
                [
                    {"type": "callback", "text": "😂 Генератор мемов", "payload": "meme_generator"},
                    {"type": "callback", "text": "📝 AI Тексты", "payload": "ai_text_gen"}
                ],
                [
                    {"type": "callback", "text": "🔮 AI Гороскоп", "payload": "ai_horoscope"},
                    {"type": "callback", "text": "ℹ️ О боте", "payload": "about_bot"}
                ]
            ]
        }
    }]

def get_back_keyboard():
    """Кнопка возврата в главное меню"""
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [{"type": "callback", "text": "🏠 Главное меню", "payload": "main_menu"}]
            ]
        }
    }]

def get_avatar_styles_keyboard():
    """Выбор стиля для AI Портрета (2x2)"""
    return [{
        "type": "inline_keyboard",
        "payload": {
            "buttons": [
                [
                    {"type": "callback", "text": "🎭 Аниме", "payload": "style_anime"},
                    {"type": "callback", "text": "🌌 Киберпанк", "payload": "style_cyberpunk"}
                ],
                [
                    {"type": "callback", "text": "🎨 Масло", "payload": "style_oil"},
                    {"type": "callback", "text": "💧 Акварель", "payload": "style_watercolor"}
                ]
            ]
        }
    }]
