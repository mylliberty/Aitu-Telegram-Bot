from azure.identity import DeviceCodeCredential
import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
SCOPES = ["https://graph.microsoft.com/.default"]

TOKEN_CACHE_FILE = os.path.join(os.getcwd(), "token_cache.json")
def save_token_cache(token_data):
    """Сохраняет access token в файл"""
    try:
        with open(TOKEN_CACHE_FILE, "w") as file:
            json.dump(token_data, file)
        print("Токен успешно сохранён в token_cache.json")
    except Exception as e:
        print(f"Ошибка при сохранении токена: {e}")
def load_token_cache():
    """Загружает access token из файла"""
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as file:
                token_data = json.load(file)
            print(f"Загруженный токен: {token_data}")
            return token_data
        except Exception as e:
            print(f"Ошибка при загрузке токена: {e}")
            return None
    print("Токен не найден, требуется новая авторизация")
    return None

# Загружаем токен из файла
cached_token = load_token_cache()

if cached_token and "access_token" in cached_token:
    access_token = cached_token["access_token"]
    print(f"Используем кешированный токен: {access_token[:10]}...")
else:
    credential = DeviceCodeCredential(client_id=CLIENT_ID, tenant_id=TENANT_ID)
    token_response = credential.get_token(" ".join(SCOPES))  # Передаём строку, а не список
    access_token = token_response.token
    save_token_cache({"access_token": access_token})

async def get_user_email():
    """Асинхронно получает email пользователя через Microsoft Graph API"""
    url = "https://graph.microsoft.com/v1.0/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                user_data = await response.json()

                if "mail" in user_data and user_data["mail"]:
                    print(f"Успешно получили email.")
                    return user_data["mail"]
                else:
                    print("Ошибка: email не найден")
                    return None
        except aiohttp.ClientError as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            return None







