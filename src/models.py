from sqlalchemy import String, Boolean, Text, Integer, ForeignKey, JSON
from .database import BaseModel
from sqlalchemy.orm import mapped_column, relationship


class User(BaseModel):
    """Модель пользователя."""

    telegram_id = mapped_column(String(length=255), nullable=False, unique=True)
    coins = relationship("CoinInfo", back_populates="user", passive_deletes=True)


class CoinInfo(BaseModel):
    """Модель информации о монете."""

    name = mapped_column(String(length=255), nullable=False)  # Название монеты
    minimum = mapped_column(String(length=255), nullable=False)   # Минимальное пороговое значение
    maximum = mapped_column(String(length=255), nullable=False)   # Максимальное пороговое значение

    user_id = mapped_column(Integer(), ForeignKey('user.id'))   # Пользователь, которому принадлежит монета
    user = relationship("User", back_populates="coins", passive_deletes=True)


class UniqueCoin(BaseModel):
    """Модель, которая описывает только уникальные монеты."""

    name = mapped_column(String(length=255), nullable=False, unique=True)
