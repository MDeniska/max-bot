"""
Все клавиатуры бота (inline-кнопки)
"""
from typing import List, Dict, Any


def get_main_menu_keyboard() -> Dict[str, Any]:
    """
    Главное меню бота - сетка кнопок 2x4
    """
    return {
        "inline_keyboard": [
            [
                {"text": "🎨 AI Аватарки", "callback_data": "ai_avatars"},
                {"text": "🖼️ Генерация картинок", "callback_data": "generate_image"}
            ],
            [
                {"text": " Генератор мемов", "callback_data": "meme_generator"},
                {"text": " AI Гороскоп", "callback_data": "ai_horoscope"}
            ],
            [
                {"text": "🤖 AI Собеседник", "callback_data": "ai_chat"},
                {"text": " AI Игры", "callback_data": "ai_games"}
            ],
            [
                {"text": "📝 AI Контент", "callback_data": "ai_content"},
                {"text": "🎁 Премиум", "callback_data": "premium"}
            ]
        ]
    }


def get_back_keyboard() -> Dict[str, Any]:
    """
    Кнопка "Назад в меню"
    """
    return {
        "inline_keyboard": [
            [{"text": "️ Назад в меню", "callback_data": "back_to_menu"}]
        ]
    }


def get_avatar_styles_keyboard() -> Dict[str, Any]:
    """
    Выбор стиля для аватарки
    """
    return {
        "inline_keyboard": [
            [
                {"text": "🎭 Аниме", "callback_data": "style_anime"},
                {"text": " Киберпанк", "callback_data": "style_cyberpunk"}
            ],
            [
                {"text": "🎨 Масло", "callback_data": "style_oil"},
                {"text": "💧 Акварель", "callback_data": "style_watercolor"}
            ],
            [
                {"text": " Супергерой", "callback_data": "style_superhero"},
                {"text": " Фэнтези", "callback_data": "style_fantasy"}
            ]
        ]
    }


def get_horoscope_types_keyboard() -> Dict[str, Any]:
    """
    Типы гаданий
    """
    return {
        "inline_keyboard": [
            [
                {"text": "♈ Гороскоп на день", "callback_data": "horoscope_daily"},
                {"text": "🔮 Расклад Таро", "callback_data": "tarot_spread"}
            ],
            [
                {"text": "🔢 Нумерология", "callback_data": "numerology"},
                {"text": "💫 Карта желаний", "callback_data": "wish_map"}
            ]
        ]
    }


def get_chat_characters_keyboard() -> Dict[str, Any]:
    """
    Персонажи для AI-чата
    """
    return {
        "inline_keyboard": [
            [
                {"text": "🧠 Психолог", "callback_data": "chat_psychologist"},
                {"text": "💼 Илон Маск", "callback_data": "chat_elon"}
            ],
            [
                {"text": "🕵️ Шерлок Холмс", "callback_data": "chat_sherlock"},
                {"text": "👨‍ Учитель", "callback_data": "chat_teacher"}
            ],
            [
                {"text": "😄 Друг", "callback_data": "chat_friend"},
                {"text": "📝 Свой персонаж", "callback_data": "chat_custom"}
            ]
        ]
    }
