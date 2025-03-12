import asyncio
from auth import get_user_email

async def main():
    email = await get_user_email()  # Добавляем await
    if email:
        role = "Студент" if email.split('@')[0].isdigit() else "Преподаватель"
        print(f"Вы авторизованы как: {role} ({email})")
    else:
        print("Не удалось получить email пользователя.")

asyncio.run(main())

