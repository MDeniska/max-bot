import os
from fastapi import FastAPI, Request, Response
import uvicorn
from maxapi import Bot, Dispatcher, types
from maxapi.filters.command import CommandStart

app = FastAPI()

# Токен из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message_created(CommandStart())
async def start_command(event: types.MessageCreated):
    await event.message.answer("🚀 Привет! Я Бизнес-Ассистент 24/7!")

# Обработчик любого текстового сообщения
@dp.message_created()
async def echo(event: types.MessageCreated):
    if event.message.body and event.message.body.text:
        await event.message.answer(f"📩 Вы написали: {event.message.body.text}")

# Эндпоинт для вебхука
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    await dp.process_update(bot, update)
    return Response(status_code=200)

@app.get("/")
def root():
    return {"status": "ok", "message": "Бот работает"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)