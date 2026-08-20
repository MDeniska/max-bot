from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    chat_id: Mapped[str] = mapped_column(String(50), index=True)
    state: Mapped[str] = mapped_column(String(50), default="idle")
    temp_data: Mapped[str] = mapped_column(String(500), nullable=True, default="")
