from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import os
import requests
from dotenv import load_dotenv
import asyncio
import redis
from handlers import router

load_dotenv()
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REDIRECT_URI = "http://localhost:5000/callback"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)

# Команда /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    access_token = r.get(user_id)  # Проверяем, есть ли токен в Redis

    if access_token:
        email = get_user_email(access_token)
        if email:
            role = define_role(email)
            await message.answer(f"Добро пожаловать, {email}!\nВаша роль: {role}.")
        else:
            await message.answer("Не удалось получить email. Попробуйте авторизоваться заново: /login")
    else:
        await message.answer("Привет! Чтобы пользоваться ботом, авторизуйтесь: /login")

# Команда /login
@router.message(Command("login"))
async def send_login_link(message: types.Message):
    auth_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope=User.Read Mail.Read"
        f"&state={message.from_user.id}"
    )
    await message.answer(f"Для авторизации перейдите по ссылке: [Войти]({auth_url})", parse_mode="Markdown")

# Функция для получения email пользователя
def get_user_email(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("mail")
    return None

# Функция для определения роли пользователя
def define_role(email):
    if email:
        local_part = email.split("@")[0]  # Берем часть до "@"
        if local_part.isdigit():  # Если только цифры, значит студент
            return "Студент"
        else:  # Если есть буквы, значит преподаватель
            return "Преподаватель / Сотрудник"
    return "Неизвестная роль"

# Команда /inbox
@router.message(Command("inbox"))
async def get_inbox(message: types.Message):
    user_id = str(message.from_user.id)
    access_token = r.get(user_id)

    if not access_token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=5&$orderby=receivedDateTime DESC"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        emails = response.json().get("value", [])
        if not emails:
            await message.answer("Входящие пусты.")
            return

        email_list = []
        for email in emails:
            subject = email.get("subject", "Без темы")
            sender = email.get("from", {}).get("emailAddress", {}).get("address", "Неизвестный отправитель")
            email_list.append(f"📩 <b>{subject}</b>\nОт: {sender}\n")

        await message.answer("\n".join(email_list), parse_mode="HTML")
    else:
        await message.answer(f"Ошибка при получении писем: {response.status_code}")


# Словарь для хранения данных о письме (user_id: {recipient, message})
email_draft = {}

# Команда /sendemail - запрос email получателя
@router.message(Command("sendemail"))
async def ask_recipient(message: types.Message):
    user_id = str(message.from_user.id)
    access_token = r.get(user_id)

    if not access_token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    email_draft[user_id] = {}  # Создаем черновик письма
    await message.answer("Введите email получателя:")


# Получаем email получателя и запрашиваем текст письма
@router.message()
async def ask_email_body(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in email_draft and "recipient" not in email_draft[user_id]:
        email_draft[user_id]["recipient"] = message.text
        await message.answer("Теперь введите текст письма:")

    elif user_id in email_draft and "recipient" in email_draft[user_id]:
        email_draft[user_id]["message"] = message.text
        recipient = email_draft[user_id]["recipient"]
        email_body = email_draft[user_id]["message"]

        result = send_email(user_id, recipient, email_body)

        if result:
            await message.answer(f"Письмо отправлено на {recipient}!")
        else:
            await message.answer("Ошибка при отправке письма. Попробуйте позже.")

        del email_draft[user_id]  # Очищаем черновик


# Функция отправки письма через Microsoft Graph API
def send_email(user_id, recipient, email_body):
    access_token = r.get(user_id)
    if not access_token:
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    email_data = {
        "message": {
            "subject": "Сообщение из Telegram бота",
            "body": {
                "contentType": "Text",
                "content": email_body
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient}}
            ]
        },
        "saveToSentItems": "true"
    }

    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    response = requests.post(url, json=email_data, headers=headers)

    return response.status_code == 202

# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)  # Очищаем старые обновления
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


