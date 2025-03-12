import os
import requests
import redis
from flask import Flask, request

app = Flask(__name__)

# Подключение к Redis с обработкой ошибок
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()  # Проверяем, что соединение установлено
except redis.ConnectionError:
    print("Ошибка подключения к Redis! Убедитесь, что сервер Redis запущен.")
    r = None

# Конфигурация OAuth
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = "http://localhost:5000/callback"

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')  # Telegram user ID

    if not code or not state:
        return "Ошибка: отсутствует код или ID пользователя", 400

    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=token_data, headers=headers)

    if response.status_code == 200:
        access_token = response.json().get("access_token")

        if r is None:
            return "Ошибка сервера: Redis недоступен", 500

        r.set(state, access_token)  # Сохраняем в Redis
        print(f"Токен сохранён в Redis: {access_token}")
        return "Авторизация успешна! Теперь можете использовать /inbox."
    else:
        return f"Ошибка при авторизации: {response.text}", 400

if __name__ == '__main__':
    app.run(debug=True)



