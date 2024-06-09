import os
import asyncio
import aiohttp
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, Update
from dotenv import load_dotenv
from aiogram import F
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
MOY_KLASS_API_KEY = os.getenv('MOY_KLASS_API_KEY')
MOY_KLASS_API_URL = 'https://api.moyklass.com/v1/'
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # URL вашего вебхука

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Вспомогательные функции для отправки сообщений
async def send_message_to_teacher(teacher_id, message):
    logger.info(f"Отправка сообщения преподавателю {teacher_id}: {message}")
    await bot.send_message(teacher_id, message)

async def send_message_to_student(student_id, message):
    logger.info(f"Отправка сообщения ученику {student_id}: {message}")
    await bot.send_message(student_id, message)

async def notify_admin(admin_id, message):
    logger.info(f"Отправка сообщения администратору {admin_id}: {message}")
    await bot.send_message(admin_id, message)

# Вспомогательная функция для отправки запросов к API "Мой класс"
async def send_api_request(endpoint, method='GET', data=None):
    logger.info(f"Отправка запроса к API 'Мой Класс': {method} {endpoint}")
    headers = {
        'Authorization': f'Bearer {MOY_KLASS_API_KEY}',
        'Content-Type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        try:
            if method == 'GET':
                async with session.get(f'{MOY_KLASS_API_URL}{endpoint}', headers=headers) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(f'{MOY_KLASS_API_URL}{endpoint}', headers=headers, json=data) as response:
                    return await response.json()
            elif method == 'PUT':
                async with session.put(f'{MOY_KLASS_API_URL}{endpoint}', headers=headers, json=data) as response:
                    return await response.json()
        finally:
            await session.close()


# Основная логика бота
async def handle_student_connection(student_id, teacher_id):
    logger.info(f"Начало обработки подключения ученика {student_id} для преподавателя {teacher_id}")
    await send_message_to_teacher(teacher_id, "Здравствуйте. Уточняю.")
    await send_message_to_student(student_id, "Здравствуйте, вы подключились?")

    await asyncio.sleep(300)  # Ждем 5 минут

    # Проверка ответа студента
    # Если студент не ответил
    await send_message_to_teacher(teacher_id, "Ученик не отвечает. Пробую связаться. Подождите, пожалуйста, еще 5 минут.")
    await send_message_to_student(student_id, "Преподаватель ожидает Вас в конференции. Вы подключаетесь?")

    await asyncio.sleep(300)  # Ждем еще 5 минут

    # Проверка ответа студента
    # Если студент не ответил
    await send_message_to_teacher(teacher_id, "Ученик не отвечает. Предлагаю перенести занятие. Ученик отменит данное занятие и выберет свободные слоты в личном кабинете, которые вы указали. Проверьте, пожалуйста, чтобы указанное время было актуальным. В карточке о занятии поставьте, что занятие было проведено, но ученик отсутствовал.")
    await send_message_to_student(student_id, "У вас сегодня было запланировано занятие. Вы не предупредили, что не сможете подключиться и не выходили на связь в назначенное время. К сожалению, в этом случае спишется оплата за урок")

@dp.message(Command(commands=['start']))
async def send_welcome(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.reply("Добро пожаловать в бот поддержки!")

@dp.message(Command(commands=['help']))
async def send_help(message: types.Message):
    logger.info(f"Получена команда /help от пользователя {message.from_user.id}")
    await message.reply("Это бот поддержки. Используйте /start для начала.")

@dp.message(F.text.lower().contains('ученик не подключается'))
async def handle_teacher_message(message: types.Message):
    teacher_id = message.from_user.id
    logger.info(f"Преподаватель {teacher_id} сообщил, что ученик не подключается")
    student_id = get_student_id_from_teacher(teacher_id)
    asyncio.create_task(handle_student_connection(student_id, teacher_id))

def get_student_id_from_teacher(teacher_id):
    # Замените это на реальную логику получения ID ученика
    logger.info(f"Получение ID ученика для преподавателя {teacher_id}")
    return 123456789

# Обработчик Webhook уведомлений от "Мой Класс"
async def handle_webhook(request):
    data = await request.json()
    logger.info(f"Получено уведомление от 'Мой Класс': {data}")
    
    if 'type' in data and data['type'] == 'message':
        sender_id = data['message']['sender_id']
        receiver_id = data['message']['receiver_id']
        text = data['message']['text']
        
        # Определите, кто отправитель и получатель
        if is_teacher(sender_id):
            await send_message_to_student(receiver_id, text)
        else:
            await send_message_to_teacher(receiver_id, text)
    
    return web.Response()

def is_teacher(user_id):
    # Логика определения, является ли пользователь учителем
    # Например, можно хранить списки ID учителей и учеников
    teachers = []
    return user_id in teachers

def is_student(user_id):
    # Логика определения, является ли пользователь студентом
    # Например, можно хранить списки ID учителей и учеников
    students = []
    return user_id in students

async def main():
    # Удаляем старый webhook, если он существует
    await bot.delete_webhook()
    
    # Устанавливаем новый webhook
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_post('/webhook', handle_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=8080)
    logger.info("Запуск вебхука")
    await site.start()

    # Закрытие вебхука и остановка приложения корректно при завершении работы
    try:
        while True:
            await asyncio.sleep(3600)  # Run for an hour, then continue
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка бота...")
    finally:
        await bot.delete_webhook()
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
