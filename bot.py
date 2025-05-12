from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import os
import requests
from dotenv import load_dotenv
import asyncio
from database import AsyncSessionLocal
from crud import get_token

load_dotenv()
router = Router()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REDIRECT_URI = "http://localhost:5000/callback"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)

# /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if access_token:
        email = get_user_email(access_token)
        if email:
            role = define_role(email)
            await message.answer(f"Добро пожаловать, {email}!\nВаша роль: {role}.")
        else:
            await message.answer("Не удалось получить email. Попробуйте авторизоваться заново: /login")
    else:
        await message.answer("Привет! Чтобы пользоваться ботом, авторизуйтесь: /login")

# /login
@router.message(Command("login"))
async def send_login_link(message: types.Message):
    auth_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&response_mode=query&scope=User.Read Mail.Read&state={message.from_user.id}"
    )
    await message.answer(f"Для авторизации перейдите по ссылке: [Войти]({auth_url})", parse_mode="Markdown")

def get_user_email(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("mail")
    return None

def define_role(email):
    if email:
        local_part = email.split("@")[0]
        if local_part.isdigit():
            return "Студент"
        else:
            return "Преподаватель / Сотрудник"
    return "Неизвестная роль"

# /events
@router.message(Command("events"))
async def get_events_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/events")
        if response.status_code != 200:
            await message.answer("Ошибка при получении данных с API.")
            return

        events = response.json()
        if not events:
            await message.answer("События не найдены.")
            return

        grouped = {
            '🇷🇺 Русский': [(e['title_ru'], e['description_ru'], e['date']) for e in events if e['title_ru'] and e['description_ru']],
            '🇬🇧 English': [(e['title_en'], e['description_en'], e['date']) for e in events if e['title_en'] and e['description_en']],
            '🇰🇿 Қазақша': [(e['title_kk'], e['description_kk'], e['date']) for e in events if e['title_kk'] and e['description_kk']],
        }

        text = "<b>📅 Предстоящие события:</b>\n\n"
        for lang, items in grouped.items():
            if items:
                text += f"<b>{lang}</b>\n"
                for i, (title, desc, date) in enumerate(items, start=1):
                    text += f"\n<b>{i}. {title}</b>\n🕓 {date}\n{desc}\n"
                text += "\n"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /faqs
@router.message(Command("faqs"))
async def get_faq_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/faqs")
        if response.status_code != 200:
            await message.answer("Ошибка при получении данных с API.")
            return

        faqs = response.json()
        if not faqs:
            await message.answer("Вопросы и ответы не найдены.")
            return

        grouped = {
            '🇷🇺 Русский': [(faq['question_ru'], faq['answer_ru']) for faq in faqs if faq['question_ru'] and faq['answer_ru']],
            '🇬🇧 English': [(faq['question_en'], faq['answer_en']) for faq in faqs if faq['question_en'] and faq['answer_en']],
            '🇰🇿 Қазақша': [(faq['question_kk'], faq['answer_kk']) for faq in faqs if faq['question_kk'] and faq['answer_kk']],
        }

        text = "<b>📚 Часто задаваемые вопросы (FAQ):</b>\n\n"
        for lang, items in grouped.items():
            if items:
                text += f"<b>{lang}</b>\n"
                for i, (q, a) in enumerate(items, start=1):
                    text += f"\n<b>{i}. {q}</b>\n{a}\n"
                text += "\n"

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /clubs
@router.message(Command("clubs"))
async def get_clubs_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/clubs")
        if response.status_code == 200:
            clubs = response.json()
            if not clubs:
                await message.answer("Клубы не найдены.")
                return

            text = "📚 Список клубов:\n\n"
            for club in clubs:
                text += (
                    f"🔸 <b>{club['name']}</b>\n"
                    f"{club['description']}\n"
                    f"<a href='{club['url']}'>Ссылка на клуб</a>\n\n"
                )
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("Ошибка при получении клубов с API.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /contacts
@router.message(Command("contacts"))
async def get_contacts_command(message: types.Message):
    try:
        response = requests.get("http://localhost:5001/api/contacts")
        if response.status_code == 200:
            contacts = response.json()
            if not contacts:
                await message.answer("Контакты не найдены.")
                return

            text = "📞 Список контактов:\n\n"
            for contact in contacts:
                text += (
                    f"🏢 <b>{contact['department']}</b>\n"
                    f"📱 Телефон: {contact['phone']}\n"
                    f"✉️ Email: {contact['email']}\n"
                    f"📂 Категория: {contact['category']}\n\n"
                )
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("Ошибка при получении контактов с API.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

# /inbox
@router.message(Command("inbox"))
async def get_inbox(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

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

# ЧЕРНОВИК письма
email_draft = {}

@router.message(Command("sendemail"))
async def ask_recipient(message: types.Message):
    user_id = str(message.from_user.id)
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

    if not access_token:
        await message.answer("Вы не авторизованы! Введите /login.")
        return

    email_draft[user_id] = {}
    await message.answer("Введите email получателя:")

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

        success = await send_email(user_id, recipient, email_body)

        if success:
            await message.answer(f"Письмо отправлено на {recipient}!")
        else:
            await message.answer("Ошибка при отправке письма. Попробуйте позже.")

        del email_draft[user_id]

# Async версия отправки email
async def send_email(user_id, recipient, email_body):
    async with AsyncSessionLocal() as session:
        access_token = await get_token(session, user_id)

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

    response = requests.post("https://graph.microsoft.com/v1.0/me/sendMail", json=email_data, headers=headers)
    return response.status_code == 202

# MAIN
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
