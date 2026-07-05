import os
from fastapi import FastAPI, Request, Response
from maxapi import Bot, Dispatcher, types
from maxapi.filters.command import CommandStart

# --- ИНИЦИАЛИЗАЦИЯ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен будем хранить в настройках Render
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---
@dp.message_created(CommandStart())
async def start_command(event: types.MessageCreated):
    await event.message.answer(
        "🚀 Привет! Я Бизнес-Ассистент 24/7.\n"
        "Я помогаю бизнесу автоматизировать работу с клиентами."
    )

@dp.message_created()
async def echo(event: types.MessageCreated):
    if event.message.body and event.message.body.text:
        await event.message.answer(f"Вы написали: {event.message.body.text}")

# --- ЭНДПОИНТ ДЛЯ ВЕБХУКА ---
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    await dp.process_update(bot, update)
    return Response(status_code=200)

# --- ТОЧКА ВХОДА ДЛЯ RENDER ---
@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))