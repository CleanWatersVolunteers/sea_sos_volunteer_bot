import re

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import StatesGroup, State
from telebot.asyncio_storage import StateMemoryStorage

from config import token, operator_bot_token

bot = AsyncTeleBot(token, state_storage=StateMemoryStorage())
operator_bot = AsyncTeleBot(operator_bot_token)


class MyStates(StatesGroup):
    write_name = State()
    write_phone = State()
    write_area = State()
    write_help = State()


work_types = [
        "Очистка пляжей от мазута", 
        "Спасение пострадавших птиц", 
        "Утилизация мазута и песка",  
        "Мониторинг состояния побережья", 
        "Информирование местных жителей",
        "Организация волонтерских штабов", 
        "Жилье для волонтеров",
        "Транспорт для волонтеров",
        "Участие в ночных сменах",
        "Сбор и передача гум. помощи",  
        "Обучение и подготовка волонтеров", 
        "Проведение замеров загрязненности",  
        "Анализ и систематизация данных", 
        "Организация экологических акций",  
        "Установка барьеров",
        "Ведение отчетности",
        "Любая другая работа"
]

regions = [
    "Анапа",
    "Витязево",
    "Веселовка",
    "Станица Благовещенская"
]


def check_phone_number(phone_number):
    phone_number = re.sub(r'D', '', phone_number).replace('+7', '8').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    print(phone_number)
    if len(phone_number) == 11 and (phone_number.startswith('8')):
        return True, phone_number
    elif len(phone_number) == 10 and phone_number.startswith('9'):
        return True, '8' + phone_number
    else:
        return False, phone_number
