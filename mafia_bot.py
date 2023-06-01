from random import randint
import os

from telebot import TeleBot, types

from settings import HELLO_MESSAGE, BOT_TOKEN, ROLES, ERROR_NUMBER_MESSAGE, FILE_NAMES
from model import Player
from utils import set_roles, check_end_game_condition_and_return_bool_and_message, \
    configure_roles, return_keyboard_with_alive_players, get_player_through_id

mafia_bot = TeleBot(BOT_TOKEN)

players_room = {}  # используется для хранения номера комнаты для пользователя
rooms = {}  # комнаты


@mafia_bot.message_handler(commands=['start', 'help'])
def start(message):
    user_id = message.from_user.id
    if message.text == '/help':
        mafia_bot.send_message(user_id, HELLO_MESSAGE)
    keyboard = types.InlineKeyboardMarkup()
    master_button = types.InlineKeyboardButton(text='Ведущий', callback_data='ведущий')
    player_button = types.InlineKeyboardButton(text='Игрок', callback_data='игрок')
    keyboard.add(master_button, player_button)
    mafia_bot.send_message(user_id, 'Выберете, за кого играть:', reply_markup=keyboard)


@mafia_bot.callback_query_handler(
    lambda call: not players_room.get(call.from_user.id) and (call.data == 'ведущий' or call.data == 'игрок'))
def chose_master_or_player(call):
    user_id = call.from_user.id
    if user_id not in players_room:  # проверка на то, чтобы игрок дважды не зашел в одну комнату
        match call.data:
            case 'ведущий':
                mafia_bot.send_message(user_id, 'Приветствую тебя, Ведущий!')

                mafia_bot.send_message(
                    user_id,
                    'Игроков должно быть не меньше трех: \n'
                    '- Мафия\n'
                    '- Шериф\n'
                    '- Мирные жители\n'
                    'Сколько будет игроков?'
                )
                mafia_bot.register_next_step_handler(call.message, handle_players)
            case 'игрок':
                mafia_bot.send_message(user_id, 'Введите номер комнаты, чтобы присоединиться')
                mafia_bot.register_next_step_handler(call.message, handle_code)
    else:
        mafia_bot.send_message(user_id, f'вы уже состоите в комнате {players_room[user_id]}')


@mafia_bot.callback_query_handler(
    lambda call: players_room.get(call.from_user.id) and (call.data == 'ведущий' or call.data == 'игрок'))
def check_again_master_or_player(call):
    user_id = call.from_user.id
    room_code = players_room[user_id]
    room = rooms[room_code]
    if user_id == room['master_id']:
        mafia_bot.send_message(user_id, f'Вы уже состоите как ведущий в комнате {room_code}, ждите...')
    else:
        mafia_bot.send_message(user_id, f'Вы уже состоите как игрок в комнате {room_code}, ждите...')


@mafia_bot.message_handler(content_types=['text'])
def help_message(message):
    match message.text:
        case _:
            mafia_bot.send_message(message.from_user.id, 'чтобы понять, как пользоваться ботом напиши `/help`')


def handle_players(message):
    user_id = message.from_user.id
    try:
        quantity_of_players = int(message.text)
    except ValueError:
        mafia_bot.send_message(user_id, ERROR_NUMBER_MESSAGE)
        mafia_bot.register_next_step_handler(message, handle_players)
    else:
        if quantity_of_players < 3:
            mafia_bot.send_message(user_id, 'игроков должно быть больше 3')
            mafia_bot.register_next_step_handler(message, handle_players)
        else:
            room_code = randint(100000, 999999)
            while room_code in rooms.keys():  # генерируем номер для случайной комнаты
                room_code = randint(100000, 999999)
            players_room[message.from_user.id] = room_code  # комната ведущего
            roles = ROLES[:]
            configure_roles(quantity_of_players, roles)
            rooms[room_code] = {
                'master_id': user_id,  # необходимо чтобы потом слать ведущему сообщения
                'quantity_of_players': quantity_of_players,
                'players': [],
                'roles': roles,
                'players_fate': {},
                'queue': 0,
                'time': 'night',
            }
            mafia_bot.send_message(user_id, f'Комната с номером `{room_code}` создана,'
                                            'поделитесь этим номером с игроками')
            # ждём, пока игроки присоединятся


def handle_code(message):
    user_id = message.from_user.id
    try:
        room_code = int(message.text)
    except ValueError:
        mafia_bot.send_message(user_id, ERROR_NUMBER_MESSAGE)
        mafia_bot.register_next_step_handler(message, handle_code)
    else:
        if room_code not in rooms.keys():
            mafia_bot.send_message(user_id, f'Комнаты {room_code} не существует! попробуйте еще раз')
        else:
            player = Player(user_id, room_code)
            rooms[room_code]['players'].append(player)
            players_room[user_id] = room_code  # назначаем игроку комнату
            mafia_bot.send_message(user_id, f'Приветствую тебя, игрок!')
            mafia_bot.send_message(user_id, f'Как тебя зовут?')
            mafia_bot.register_next_step_handler(message, handle_name)


def handle_name(message):
    user_id = message.from_user.id
    name = message.text
    player = get_player_through_players_room(user_id)
    player.name = name  # Сохраняем игроку имя
    mafia_bot.send_message(user_id, f'Ждём других игроков...')
    room = rooms[player.room_code]
    if len(room['players']) >= room['quantity_of_players']:
        # говорим ведущему, что все в сборе
        master_id = room['master_id']
        players_name = [player.name for player in room['players']]
        mafia_bot.send_message(master_id, f'Игроки собрались: {", ".join(players_name)}')
        mafia_bot.send_message(master_id, 'Раздаем роли')
        # назначаем роли
        set_roles(room['players'], room['roles'])
        mafia_bot.send_message(master_id, 'Роли розданы:')
        # рассылаем роли мастеру и всем игрокам
        for player in room['players']:
            mafia_bot.send_message(master_id, f'{player.name}: {player.role}')
            file_path = os.path.join('images', f'{FILE_NAMES[player.role]}.png')
            with open(file_path, 'rb') as img:
                mafia_bot.send_photo(player.id, img)
            mafia_bot.send_message(player.id, f'Вы {player.role}')
            mafia_bot.send_message(player.id, 'Наступает ночь, город засыпает...')

        # игра
        keyboard = types.InlineKeyboardMarkup()
        go_button = types.InlineKeyboardButton(text='Начать игру!', callback_data='night')
        keyboard.add(go_button)
        mafia_bot.send_message(master_id, 'Начинаем?', reply_markup=keyboard)


@mafia_bot.callback_query_handler(lambda call: players_room.get(call.from_user.id) and call.data == 'night')
def handle_night(call):
    room_code = players_room[call.from_user.id]
    room = rooms[room_code]
    alive_players = [player for player in room['players'] if player.is_alive]

    role = room['roles'][room['queue']]
    for player in alive_players:
        mafia_bot.send_message(player.id, f'Ходит {role}')  # можно картиночку послать ночи

    players_with_role = list(filter(lambda player: player.role == role and player.is_alive, room['players']))
    action_message = {
        'Мафия': 'выберете кого убить...',
        'Доктор': 'выберете кого спасти...',
        'Шериф': 'выберете кого арестовать...'
    }

    for player in players_with_role:
        keyboard = return_keyboard_with_alive_players(room['players'], player)
        mafia_bot.send_message(player.id, action_message[role], reply_markup=keyboard)


def check_list_names(call):
    return players_room.get(call.from_user.id) and \
        call.data != 'day' and call.data != 'night' and call.data != 'ведущий' and call.data != 'игрок' and \
        int(call.data) in [player.id for player in rooms[players_room[call.from_user.id]]['players']]


@mafia_bot.callback_query_handler(check_list_names)
def night_action(call):
    player = get_player_through_players_room(call.from_user.id)
    room = rooms[player.room_code]

    dependent_player = get_player_through_id(room['players'], int(call.data))
    room['players_fate'][player.role] = [dependent_player]

    end_queue = len(room['roles']) - 1
    if room['queue'] < end_queue:
        room['queue'] += 1
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Передать ход', callback_data='night')
        keyboard.add(next_button)
        mafia_bot.send_message(player.id, f'Вы выбрали {dependent_player.name}', reply_markup=keyboard)
    else:
        room['queue'] = 0
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Дождаться утра', callback_data='day')
        keyboard.add(next_button)
        for each_player in room['players']:
            mafia_bot.send_message(each_player.id, 'Наступает день... город просыпается')
        mafia_bot.send_message(room['master_id'], 'Наступает день... город просыпается')
        mafia_bot.send_message(player.id, f'Вы выбрали {dependent_player.name}', reply_markup=keyboard)


@mafia_bot.callback_query_handler(lambda call: players_room.get(call.from_user.id) and call.data == 'day')
def handle_day(call):
    room_code = players_room[call.from_user.id]
    room = rooms[room_code]
    end_game, message = check_end_game_condition_and_return_bool_and_message(room)

    mafia_bot.send_message(room['master_id'], message)  # отдельно шлем мастеру
    for player in room['players']:
        mafia_bot.send_message(player.id, message)
    if not end_game:
        for player in room['players']:
            mafia_bot.send_message(player.id, 'Наступает ночь, город засыпает...')
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Продолжить!', callback_data='night')
        keyboard.add(next_button)
        mafia_bot.send_message(room['master_id'], 'Наступает ночь, город засыпает...', reply_markup=keyboard)
    else:  # заканчиваем игру
        for player in room['players']:
            mafia_bot.send_message(player.id, 'Спасибо за игру!!!')
        mafia_bot.send_message(room['master_id'], 'Спасибо за игру!!!')  # отдельно шлем мастеру
        # очищаем пользователей
        for player in room['players']:
            del players_room[player.id]
        del players_room[room['master_id']]  # очищаем мастера
        del rooms[room_code]  # удаляем комнату


def get_player_through_players_room(user_id) -> Player:
    room_code = players_room[user_id]
    all_players = rooms[room_code]['players']
    for i in range(len(all_players)):
        if all_players[i].id == user_id:
            return all_players[i]


if __name__ == '__main__':
    mafia_bot.polling(none_stop=True, interval=0)
