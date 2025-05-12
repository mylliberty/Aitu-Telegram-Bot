import os
import aiohttp
from flask import Flask, request
from sqlalchemy.ext.asyncio import AsyncSession
from models import UserToken  # Убедитесь, что ваша модель правильно определена
from database import AsyncSessionLocal  # Ваше подключение к базе данных

app = Flask(__name__)

# Конфигурация OAuth
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = "http://localhost:5000/callback"

# Асинхронная функция для получения токена
async def get_access_token(code, state):
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=token_data, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

# Сохранение токена в базу данных PostgreSQL
async def save_token_to_db(session: AsyncSession, user_id: str, access_token: str):
    token = UserToken(user_id=user_id, token=access_token)  # Убедитесь, что 'token' — это правильное имя поля в модели
    session.add(token)
    await session.commit()

# Маршрут callback
@app.route('/callback')
async def callback():
    code = request.args.get('code')
    state = request.args.get('state')  # Telegram user ID

    if not code or not state:
        return "Ошибка: отсутствует код или ID пользователя", 400

    # Асинхронный запрос к API для получения токена
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token", data=token_data) as response:
            if response.status == 200:
                result = await response.json()
                access_token = result.get("access_token")

                # Сохраняем токен в базу данных
                async with AsyncSessionLocal() as db_session:
                    await save_token_to_db(db_session, state, access_token)

                return "Авторизация успешна! Теперь можете использовать /inbox."
            else:
                return f"Ошибка при авторизации: {response.text}", 400

if __name__ == '__main__':
    app.run(debug=True)




