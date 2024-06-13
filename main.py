import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommandScopeAllPrivateChats
from dotenv import load_dotenv
import logging
import asyncio

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токены и URL из переменных окружения
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
MOY_KLASS_API_KEY = os.getenv('MOY_KLASS_API_KEY')
MOY_KLASS_API_URL = os.getenv('MOY_KLASS_API_URL')

# Создаем экземпляр бота
bot = Bot(token=TELEGRAM_API_TOKEN)

async def get_token():
    url = f"{MOY_KLASS_API_URL}/v1/company/auth/getToken"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'apiKey': MOY_KLASS_API_KEY
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('accessToken')
                else:
                    logging.error(f"Failed to fetch token: {response.status}")
                    return None
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Connection error while fetching token: {e}")
        return None

async def get_classes(token):
    url = f"{MOY_KLASS_API_URL}/v1/company/classes"
    headers = {
        'x-access-token': token
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    logging.error("Unauthorized: Check your API key.")
                    return None
                else:
                    logging.error(f"Failed to fetch classes: {response.status}")
                    return None
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Connection error: {e}")
        return None

async def send_classes(message: types.Message):
    token = await get_token()
    if not token:
        await message.reply("Не удалось получить токен. Проверьте подключение, URL API и API ключ.")
        return
    
    classes = await get_classes(token)
    if not classes:
        await message.reply("Не удалось получить список групп. Проверьте подключение, URL API и API ключ.")
        return

    response_text = "Список групп:\n"
    for class_group in classes:
        response_text += (
            f"ID: {class_group['id']}\n"
            f"Название: {class_group.get('name', 'Не указано')}\n"
            f"Статус: {class_group['status']}\n"
            f"Начало занятий: {class_group.get('beginDate', 'Не указано')}\n"
            f"Макс. студентов: {class_group.get('maxStudents', 'Не указано')}\n"
            f"Цена: {class_group.get('price', 'Не указано')}\n"
            f"ID филиала: {class_group['priceForWidget']}\n\n"
        )

    await message.reply(response_text)

async def main():
    logging.basicConfig(level=logging.INFO)
    # Инициализируем диспетчер
    dp = Dispatcher()
    
    # Регистрируем обработчик команды /classes
    dp.message.register(send_classes, Command('classes'))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
