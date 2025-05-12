# crud.py
from sqlalchemy.future import select
from models import UserToken
from database import AsyncSession

async def get_token(session: AsyncSession, user_id: str):
    result = await session.execute(select(UserToken).where(UserToken.user_id == user_id))
    token = result.scalar_one_or_none()
    return token.token if token else None

async def save_token(session: AsyncSession, user_id: str, access_token: str):
    token = await session.get(UserToken, user_id)
    if token:
        token.access_token = access_token
    else:
        token = UserToken(user_id=user_id, token=access_token)
        session.add(token)
    await session.commit()
