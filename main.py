# ====================================================================================

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

# ====================================================================================

# Получаем токены и URL из переменных окружения
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
MOY_KLASS_API_KEY = os.getenv('MOY_KLASS_API_KEY')
MOY_KLASS_API_URL = os.getenv('MOY_KLASS_API_URL')

# Создаем экземпляр бота
bot = Bot(token=TELEGRAM_API_TOKEN)

# ====================================================================================

# Функция для разбиения длинного сообщения на части
def split_message(text, max_length=4096):
    parts = []
    while len(text) > max_length:
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:]
    parts.append(text)
    return parts

# ====================================================================================

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

# ====================================================================================

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

# ====================================================================================

async def get_students(token):
    url = f"{MOY_KLASS_API_URL}/v1/company/users"
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
                    logging.error(f"Failed to fetch students: {response.status}")
                    return None
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Connection error: {e}")
        return None

# ====================================================================================

async def get_lessons(token, params):
    url = f"{MOY_KLASS_API_URL}/v1/company/lessons"
    headers = {
        'x-access-token': token
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    logging.error("Unauthorized: Check your API key.")
                    return None
                else:
                    logging.error(f"Failed to fetch lessons: {response.status}")
                    return None
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Connection error: {e}")
        return None

# ====================================================================================

async def get_lesson_info(token, lesson_id, params):
    url = f"{MOY_KLASS_API_URL}/v1/company/lessons/{lesson_id}"
    headers = {
        'x-access-token': token
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    logging.error("Unauthorized: Check your API key.")
                    return None
                else:
                    logging.error(f"Failed to fetch lesson info: {response.status}")
                    return None
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Connection error: {e}")
        return None

# ====================================================================================

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
            f"ID филиала: {class_group['filialId']}\n\n"
        )

    for part in split_message(response_text):
        await message.reply(part)

# ====================================================================================

async def send_students(message: types.Message):
    token = await get_token()
    if not token:
        await message.reply("Не удалось получить токен. Проверьте подключение, URL API и API ключ.")
        return
    
    students = await get_students(token)
    if not students:
        await message.reply("Не удалось получить список учеников. Проверьте подключение, URL API и API ключ.")
        return

    response_text = "Список учеников:\n"
    for student in students.get('users', []):
        response_text += (
            f"ID: {student['id']}\n"
            f"Имя: {student.get('name', 'Не указано')}\n"
            f"Email: {student.get('email', 'Не указано')}\n"
            f"Телефон: {student.get('phone', 'Не указано')}\n"
            f"Дата создания: {student.get('createdAt', 'Не указано')}\n"
            f"Дата изменения: {student.get('updatedAt', 'Не указано')}\n\n"
        )

    for part in split_message(response_text):
        await message.reply(part)

# ====================================================================================

async def send_lessons(message: types.Message):
    # Разбор аргументов команды
    args = message.text.split()[1:]
    params = {}

    for arg in args:
        key, value = arg.split('=')
        if key in ['date', 'lessonId', 'roomId', 'filialId', 'classId', 'teacherId']:
            params[key] = value.split(',')
        elif key in ['statusId', 'userId', 'offset', 'limit']:
            params[key] = int(value)
        elif key in ['includeRecords', 'includeWorkOffs', 'includeMarks', 'includeTasks', 'includeTaskAnswers', 'includeUserSubscriptions', 'includeParams']:
            params[key] = value.lower() == 'true'

    token = await get_token()
    if not token:
        await message.reply("Не удалось получить токен. Проверьте подключение, URL API и API ключ.")
        return

    lessons = await get_lessons(token, params)
    if not lessons:
        await message.reply("Не удалось получить список занятий. Проверьте подключение, URL API и API ключ.")
        return

    response_text = "Список занятий:\n"
    for lesson in lessons.get('lessons', []):
        response_text += (
            f"ID: {lesson.get('id', 'Не указано')}\n"
            f"Дата: {lesson.get('date', 'Не указано')}\n"
            f"Время начала: {lesson.get('beginTime', 'Не указано')}\n"
            f"Время окончания: {lesson.get('endTime', 'Не указано')}\n"
            f"Создано: {lesson.get('createdAt', 'Не указано')}\n"
            f"ID филиала: {lesson.get('filialId', 'Не указано')}\n"
            f"ID аудитории: {lesson.get('roomId', 'Не указано')}\n"
            f"ID группы: {lesson.get('classId', 'Не указано')}\n"
            f"Статус: {'Проведено' if lesson.get('status') == 1 else 'Не проведено'}\n"
            f"Комментарий: {lesson.get('comment', 'Не указан')}\n"
            f"Максимум студентов: {lesson.get('maxStudents', 'Не указано')}\n"
            f"Тема: {lesson.get('topic', 'Не указана')}\n"
            f"Описание: {lesson.get('description', 'Не указано')}\n"
            f"Учителя: {', '.join(map(str, lesson.get('teacherIds', ['Не указаны']))) }\n"
            f"Записи: {lesson.get('records', 'Не указаны')}\n"
            f"Домашнее задание: {lesson.get('homeTask', 'Не указано')}\n"
            f"Задание на занятие: {lesson.get('lessonTask', 'Не указано')}\n"
            f"Оценки: {lesson.get('marks', 'Не указаны')}\n"
            f"Ответы на задания: {lesson.get('answers', 'Не указаны')}\n\n"
        )

    for part in split_message(response_text):
        await message.reply(part)

# ====================================================================================

async def send_lessons_ids(message: types.Message):
    args = message.text.split()[1:]
    params = {
        "limit": 500  # Максимальный лимит, чтобы получить как можно больше занятий
    }

    # Проверяем, есть ли в аргументах даты
    if len(args) >= 1:
        params['date'] = args[:2]  # Берем максимум два значения даты

    token = await get_token()
    if not token:
        await message.reply("Не удалось получить токен. Проверьте подключение, URL API и API ключ.")
        return

    lessons = await get_lessons(token, params)
    if not lessons:
        await message.reply("Не удалось получить список занятий. Проверьте подключение, URL API и API ключ.")
        return

    lessons_ids = [lesson['id'] for lesson in lessons.get('lessons', [])]
    response_text = "Список ID занятий:\n" + "\n".join(map(str, lessons_ids))

    for part in split_message(response_text):
        await message.reply(part)

# ====================================================================================

async def send_lesson_info(message: types.Message):
    args = message.text.split()[1:]
    if not args:
        await message.reply("Укажите ID занятия.")
        return

    lesson_id = args[0]
    params = {}

    for arg in args[1:]:
        key, value = arg.split('=')
        if key in ['includeRecords', 'includeWorkOffs', 'includeMarks', 'includeTasks', 'includeTaskAnswers', 'includeParams']:
            params[key] = value.lower() == 'true'

    token = await get_token()
    if not token:
        await message.reply("Не удалось получить токен. Проверьте подключение, URL API и API ключ.")
        return

    lesson_info = await get_lesson_info(token, lesson_id, params)
    if not lesson_info:
        await message.reply("Не удалось получить информацию о занятии. Проверьте подключение, URL API и API ключ.")
        return

    response_text = (
        f"ID: {lesson_info.get('id', 'Не указано')}\n"
        f"Дата: {lesson_info.get('date', 'Не указано')}\n"
        f"Время начала: {lesson_info.get('beginTime', 'Не указано')}\n"
        f"Время окончания: {lesson_info.get('endTime', 'Не указано')}\n"
        f"Создано: {lesson_info.get('createdAt', 'Не указано')}\n"
        f"ID филиала: {lesson_info.get('filialId', 'Не указано')}\n"
        f"ID аудитории: {lesson_info.get('roomId', 'Не указано')}\n"
        f"ID группы: {lesson_info.get('classId', 'Не указано')}\n"
        f"Статус: {'Проведено' if lesson_info.get('status') == 1 else 'Не проведено'}\n"
        f"Комментарий: {lesson_info.get('comment', 'Не указан')}\n"
        f"Максимум студентов: {lesson_info.get('maxStudents', 'Не указано')}\n"
        f"Тема: {lesson_info.get('topic', 'Не указана')}\n"
        f"Описание: {lesson_info.get('description', 'Не указано')}\n"
        f"Учителя: {', '.join(map(str, lesson_info.get('teacherIds', ['Не указаны']))) }\n"
        f"Записи: {lesson_info.get('records', 'Не указаны')}\n"
        f"Домашнее задание: {lesson_info.get('homeTask', 'Не указано')}\n"
        f"Задание на занятие: {lesson_info.get('lessonTask', 'Не указано')}\n"
        f"Оценки: {lesson_info.get('marks', 'Не указаны')}\n"
        f"Ответы на задания: {lesson_info.get('answers', 'Не указаны')}\n"
    )

    for part in split_message(response_text):
        await message.reply(part)

# ====================================================================================

async def main():
    logging.basicConfig(level=logging.INFO)
    # Инициализируем диспетчер
    dp = Dispatcher()
    
    # Регистрируем обработчики команд
    dp.message.register(send_classes, Command('classes'))
    dp.message.register(send_students, Command('students'))
    dp.message.register(send_lessons, Command('lessons'))
    dp.message.register(send_lessons_ids, Command('lessons_ids'))
    dp.message.register(send_lesson_info, Command('lesson_info')) 

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ====================================================================================

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")

# ====================================================================================
