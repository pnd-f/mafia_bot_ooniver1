import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

HELLO_MESSAGE = 'Mafia_bot приветствует тебя! Если ты Ведущий, нажми кнопку "ведущий", если игрок - "игрок"'
ROLES = ['Мафия', 'Шериф']
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEBUG = bool(int(os.getenv('DEBUG')))
DEBUG_ROOM_CODE = 123321
FACTORY_USER_ID = os.getenv('FACTORY_USER_ID')
ERROR_NUMBER_MESSAGE = 'Ошибка!!! Введите число!!'
