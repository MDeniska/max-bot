# Используем официальный Python-образ (легкий и стабильный)
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости (если нужны для некоторых библиотек)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей СНАЧАЛА (для кэширования слоев Docker)
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Создаем папку для базы данных (если используется SQLite)
RUN mkdir -p /app/data && chmod 777 /app/data

# Открываем порт (Bothost сам пробросит его наружу)
EXPOSE 3000

# Команда запуска приложения
CMD ["python", "bot.py"]
