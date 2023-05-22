from time import sleep
from random import randint

from telebot import TeleBot, types

from const import HELLO_MESSAGE, BOT_TOKEN
from model import Player
from temp import get_mock_players
from utils import set_roles

mafia_bot = TeleBot(BOT_TOKEN)

players_room = {}  # используется для хранения номера комнаты
rooms = {}  # комнаты


@mafia_bot.message_handler(content_types=['text', 'document'])
def start(message):
    if not message.from_user.id in players_room:

        match message.text:
            case '/help':
                mafia_bot.send_message(message.from_user.id, HELLO_MESSAGE)

            case 'Ведущий' | 'ведущий':
                mafia_bot.send_message(message.from_user.id, 'Приветствую тебя, Ведущий!')

                mafia_bot.send_message(
                    message.from_user.id,
                    'Игроков должно быть не меньше трех: \n'
                    '- Мафия\n'
                    '- Шериф\n'
                    '- Мирные граждане\n'
                    'Сколько будет игроков?'
                )
                mafia_bot.register_next_step_handler(message, handle_players)

            case 'Игрок' | 'игрок':
                mafia_bot.send_message(message.from_user.id, 'Введите номер комнаты, чтобы присоединиться')
                mafia_bot.register_next_step_handler(message, handle_code)
            case _:
                mafia_bot.send_message(message.from_user.id, 'чтобы понять, как пользоваться ботом напиши `/help`')
    else:
        mafia_bot.send_message(message.from_user.id, f'Вы еще играете в комнате {players_room[message.from_user.id]}')


def handle_players(message):
    count = int(message.text)
    if count < 3:
        mafia_bot.send_message(message.from_user.id, 'игроков должно быть больше 3')
        mafia_bot.register_next_step_handler(message, handle_players)
    else:
        code_room = randint(100000, 999999)
        while code_room in rooms.keys():  # генерируем номер для случайной комнаты
            code_room = randint(100000, 999999)
        rooms[code_room] = {
            'master_id': message.from_user.id,  # необходимо чтобы потом слать ведущему сообщения
            'count_for_play': count,
            'players': get_mock_players(),  # debugging
            # 'players': [],
            'ready_for_play': False
        }
        mafia_bot.send_message(message.from_user.id, f'Комната с номером `{code_room}` создана,'
                                                     'поделитесь этим номером с игроками')
        # ждем других игроков
        while not rooms[code_room]['ready_for_play']:
            sleep(1)
        players_name = [player.name for player in rooms[code_room]['players']]
        mafia_bot.send_message(message.from_user.id, f'Игроки собрались: {", ".join(players_name)}')
        mafia_bot.send_message(message.from_user.id, 'Раздаем роли')
        set_roles(rooms[code_room]['players'])
        mafia_bot.send_message(message.from_user.id, 'Роли розданы:')
        for player in rooms[code_room]['players']:
            mafia_bot.send_message(message.from_user.id, f'{player.name}: {player.role}')
            with open(f'images/{player.role}.png', 'rb') as img:
                mafia_bot.send_photo(player.id, img)
            mafia_bot.send_message(player.id, f'Вы {player.role}')


def handle_code(message):
    code_room = int(message.text)
    if code_room not in rooms.keys():
        mafia_bot.send_message(message.from_user.id, f'Комнаты {code_room} не существует! попробуйте еще раз')
    else:
        player = Player(message.from_user.id, code_room)
        players_room[message.from_user.id] = code_room  # помещаем комнаты для юзера, чтобы пробросить в следующую функцию
        rooms[code_room]['players'].append(player)
        mafia_bot.send_message(message.from_user.id, f'Введите своё имя')
        mafia_bot.register_next_step_handler(message, handle_name)


def handle_name(message):
    name = message.text
    player = get_player_through_message(message)
    player.name = name
    code_room = players_room[message.from_user.id]
    mafia_bot.send_message(message.from_user.id, f'Ждём других игроков...')
    if len(rooms[code_room]['players']) >= rooms[code_room]['count_for_play']:
        rooms[code_room]['ready_for_play'] = True


def get_player_through_message(message):
    code_room = players_room[message.from_user.id]
    all_players = rooms[code_room]['players']
    for i in range(len(all_players)):
        if all_players[i].id == message.from_user.id:
            return all_players[i]


if __name__ == '__main__':
    mafia_bot.polling(none_stop=True, interval=0)

