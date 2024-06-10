import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from ..database import async_session
from ..models import User, CoinInfo, UniqueCoin
from ..coin_api_logic.coin import CoinMarket
from ..settings import MARKET_UPDATE_TIME_SECONDS

start_router = Router()

load_dotenv()

coin_m = CoinMarket(api_key=os.getenv("COIN_MARKET_API_TOKEN"))


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    """Стартовая точка бота."""

    await message.answer("Добро пожаловать в бот, который может отслеживать изменение стоимости монеты относительно USD"
                         "на сайте: https://coinmarketcap.com/")

    kb = [
        [KeyboardButton(text="Мои монеты")],
        [KeyboardButton(text="Добавить монету")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(f"Выберите пункт меню:", reply_markup=keyboard)


class AddCoin(StatesGroup):
    coin_name = State()
    coin_minimal = State()
    coin_maximum = State()


@start_router.message(F.text == 'Мои монеты')
async def get_coins(message: Message, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        current_user_id = str(message.from_user.id)

        user = await session.execute(select(User).where(User.telegram_id == current_user_id))
        try:
            coins = await session.execute(select(CoinInfo).where(CoinInfo.user_id == user.fetchone()[0].id))
        except TypeError:
            user = User(telegram_id=current_user_id)
            session.add(user)
            await session.commit()

            user = await session.execute(select(User).where(User.telegram_id == current_user_id))
            coins = await session.execute(select(CoinInfo).where(CoinInfo.user_id == user.fetchone()[0].id))
        coins = coins.scalars().all()

        await message.answer(f" Вот все ваши монеты: {[coin.name for coin in coins]}")


@start_router.message(F.text == 'Добавить монету')
async def add_coin(message: Message, state: FSMContext):
    async with async_session() as session:
        current_user_id = str(message.from_user.id)

        user = await session.execute(select(User).where(User.telegram_id == current_user_id))
        try:
            user = user.fetchone()[0]
        except TypeError:
            user = User(telegram_id=current_user_id)
            session.add(user)
            await session.commit()

        await message.answer("Введите сокращённое название монеты (например: BTC - Bitcoin): ",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(AddCoin.coin_name)


@start_router.message(AddCoin.coin_name)
async def add_coin(message: Message, state: FSMContext):
    await state.update_data(coin_name=message.text)

    await message.answer(f"Вы указали следующую монету: {message.text}, её актуальная стоимость в USD:"
                         f" {coin_m.get_current_price(symbol=[message.text])} \n"
                         f"Укажите минимальную стоимость выбранной монеты, при которой нужно отправить"
                         f" уведомление (Если этот пункт не нужен поставьте 0): ")
    await state.set_state(AddCoin.coin_minimal)


@start_router.message(AddCoin.coin_minimal)
async def add_coin_minimal(message: Message, state: FSMContext):
    await state.update_data(coin_minimal=message.text)

    await message.answer(f"Вы указали минимальное число: {message.text} \n"
                         f"Теперь укажите максимальную стоимость выбранной монеты,"
                         f" при которой нужно отправить уведомление (Если этот пункт не нужен поставьте 0): ")
    await state.set_state(AddCoin.coin_maximum)


@start_router.message(AddCoin.coin_maximum)
async def save_coin(message: Message, state: FSMContext):
    await state.update_data(coin_maximum=message.text)
    data = await state.get_data()

    current_user_id = str(message.from_user.id)

    async with async_session() as session:
        user = await session.execute(select(User).where(User.telegram_id == current_user_id))
        user = user.fetchone()[0]

        try:
            coin = await session.execute(select(CoinInfo).where((CoinInfo.user_id == user.id)
                                                                & (CoinInfo.name == data['coin_name'])))
            coin = coin.fetchone()[0]
            await message.answer(f"Эта монета: {coin.name} уже добавлена в отслеживание!")
            await state.clear()
        except TypeError:
            coin = CoinInfo(name=data['coin_name'], maximum=data['coin_maximum'],
                            minimum=data['coin_minimal'], user_id=user.id)
            session.add(coin)

            uniq_coin = await session.execute(select(UniqueCoin).where(UniqueCoin.name == coin.name))
            uniq_coin = uniq_coin.fetchone()

            if not uniq_coin:
                uniq_coin = UniqueCoin(name=coin.name)
                session.add(uniq_coin)

        await state.clear()
        await session.commit()

        await message.answer(f"Вы указали все необходимые данные! {data}. \n"
                             f"Информация о монете была успешно сохранена ")
        await message.answer(f"Монета будет обновляться каждые {MARKET_UPDATE_TIME_SECONDS} секунд.")

