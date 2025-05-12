from sqlalchemy import Column, String
from database import Base  # Используем общий Base

class UserToken(Base):
    __tablename__ = 'user_tokens'

    user_id = Column(String, primary_key=True)
    token = Column(String)

    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token

