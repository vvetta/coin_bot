from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


from . import settings


class BaseModel(DeclarativeBase):
    """
    Базовый абстрактный класс моделей приложения.
    """

    # Показывает, что класса является абстрактным и что его не нужно создавать.
    __abstract__ = True

    # Автоматически создаёт имя таблицы на основе имени класса.
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    # Базовые колонки, которые будут повторяться во всех моделях.
    id = Column(Integer, primary_key=True, index=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())


async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
