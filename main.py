import os
import asyncio
import logging
from sqlalchemy import select
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.models import User, UniqueCoin, CoinInfo
from src.database import async_engine, BaseModel, async_session
from src.handlers.start import start_router
from src.coin_api_logic.coin import CoinMarket
from src.settings import MARKET_UPDATE_TIME_SECONDS
# from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def init_models():
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

load_dotenv()

# scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
admins = [int(admin_id) for admin_id in os.getenv('ADMINS').split(',')]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=os.getenv('TELEGRAM_BOT_API_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


coin_m = CoinMarket(api_key=os.getenv("COIN_MARKET_API_TOKEN"))


async def periodic_task(interval):
    while True:
        async with async_session() as session:
            coins = await session.execute(select(UniqueCoin))
            coins = [coin.name for coin in coins.scalars().all()]

            data = coin_m.get_current_price(symbol=coins)

            users = await session.execute(select(User))
            users = users.scalars().all()

            for user in users:

                user_coins = await session.execute(select(CoinInfo).where(CoinInfo.user_id == user.id))
                user_coins = user_coins.scalars().all()

                for user_coin in user_coins:
                    if data.get(user_coin.name):
                        if data[user_coin.name] <= float(user_coin.minimum):
                            await bot.send_message(user.telegram_id,
                                                   f"Стоимость монеты упала ниже указанного вами минимума! \n"
                                                   f"стоимость монеты - {data[user_coin.name]} | "
                                                   f"указанный минимум - {user_coin.minimum}")
                        elif data[user_coin.name] >= float(user_coin.maximum):
                            await bot.send_message(user.telegram_id,
                                                   f"Стоимость монеты поднялась выше указанного вами максимума! \n"
                                                   f"стоимость монеты - {data[user_coin.name]} | "
                                                   f"указанный максимум - {user_coin.maximum}")
                        else:
                            await bot.send_message(user.telegram_id,
                                                   f"Актуальная стоимость монеты: {data[user_coin.name]}")
        await asyncio.sleep(interval)  # Пауза между отправками


async def main():
    dp.include_router(start_router)
    await bot.delete_webhook(drop_pending_updates=True)
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_task(MARKET_UPDATE_TIME_SECONDS))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(init_models())
    asyncio.run(main())
