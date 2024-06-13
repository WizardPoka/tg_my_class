import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из .env файла
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WAZZUP_API_KEY = os.getenv('WAZZUP_API_KEY')
MY_CLASS_API_URL = os.getenv('MY_CLASS_API_URL')
MY_CLASS_API_KEY = os.getenv('MY_CLASS_API_KEY')

bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Вспомогательные функции для работы с API "Мой класс"
async def get_lessons():
    logger.info("Запрос списка занятий через API 'Мой класс'")
    # Пример запроса к API "Мой класс"
    # response = requests.get(f"{MY_CLASS_API_URL}/lessons", headers={"Authorization": f"Bearer {MY_CLASS_API_KEY}"})
    # return response.json()
    return []

async def notify_users_about_lessons():
    lessons = await get_lessons()
    for lesson in lessons:
        student_id = lesson['student_id']
        teacher_id = lesson['teacher_id']
        message = f"У вас запланировано занятие с преподавателем {teacher_id}"
        await send_message_to_student(student_id, message)

# Вспомогательные функции для отправки сообщений
async def send_message_to_teacher(teacher_id, message):
    logger.info(f"Отправка сообщения преподавателю {teacher_id}: {message}")
    await bot.send_message(teacher_id, message)

async def send_message_to_student(student_id, message):
    logger.info(f"Отправка сообщения ученику {student_id}: {message}")
    await bot.send_message(student_id, message)

# Основная логика бота
@dp.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.reply("Добро пожаловать в поддерживающий бот!")

@dp.message(Command(commands=['help']))
async def send_help(message: types.Message):
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    await message.reply("Это поддерживающий бот. Используйте /start, чтобы начать.")

@dp.message(lambda message: 'ученик не подключается' in message.text.lower())
async def handle_teacher_message(message: types.Message):
    teacher_id = message.from_user.id
    logger.info(f"Преподаватель {teacher_id} сообщил, что ученик не подключается")
    student_id = get_student_id_from_teacher(teacher_id)
    asyncio.create_task(handle_student_connection(student_id, teacher_id))
    await message.reply("Сообщение принято, начинаю обработку.")

def get_student_id_from_teacher(teacher_id):
    logger.info(f"Получение ID ученика для преподавателя {teacher_id}")
    return 123456789

# Обработчик Webhook уведомлений от Wazzup
async def handle_webhook(request):
    data = await request.json()
    logger.info(f"Получено уведомление от Wazzup: {data}")
    
    if 'type' in data and data['type'] == 'message':
        sender_id = data['message']['sender_id']
        receiver_id = data['message']['receiver_id']
        text = data['message']['text']
        
        logger.info(f"Получено сообщение от {sender_id} к {receiver_id}: {text}")

        if is_teacher(sender_id):
            await send_message_to_student(receiver_id, text)
        else:
            await send_message_to_teacher(receiver_id, text)
    
    return web.Response()

def is_teacher(user_id):
    teachers = []
    return user_id in teachers

def is_student(user_id):
    students = []
    return user_id in students

async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    # Устанавливаем новый webhook
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_post('/webhook', handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=8080)
    logger.info("Запуск вебхука")
    await site.start()

    logger.info("Бот запущен и работает")
    try:
        while True:
            await notify_users_about_lessons()
            await asyncio.sleep(3600)  # Run every hour
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка бота...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
