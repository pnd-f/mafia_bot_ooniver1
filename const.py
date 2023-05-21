import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

HELLO_MESSAGE = 'Mafia_bot приветствует тебя! Если ты Ведущий, введи строку "ведущий", если игрок - "игрок"'
ROLES = ['mafia', 'sherif']
BOT_TOKEN = os.getenv('BOT_TOKEN')
