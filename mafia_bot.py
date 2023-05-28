from time import sleep
from random import randint

from telebot import TeleBot, types

from settings import HELLO_MESSAGE, BOT_TOKEN, DEBUG, ROLES, ERROR_NUMBER_MESSAGE, DEBUG_ROOM_CODE
from model import Player
from player_factory import get_mock_players
from utils import set_roles, get_players_status, check_end_game_condition_and_return_bool_and_message, \
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


@mafia_bot.callback_query_handler(lambda call: call.data == 'ведущий' or call.data == 'игрок')
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
                    '- Мирные граждане\n'
                    'Сколько будет игроков?'
                )
                mafia_bot.register_next_step_handler(call.message, handle_players)
            case 'игрок':
                mafia_bot.send_message(user_id, 'Введите номер комнаты, чтобы присоединиться')
                mafia_bot.register_next_step_handler(call.message, handle_code)
    else:
        mafia_bot.send_message(user_id, f'вы уже состоите в комнате {players_room[user_id]}')


@mafia_bot.message_handler(content_types=['text'])
def help_command(message):
    match message.text:
        case '/help':
            mafia_bot.send_message(message.from_user.id, HELLO_MESSAGE)
        case _:
            mafia_bot.send_message(message.from_user.id, 'чтобы понять, как пользоваться ботом напиши `/help`')


def handle_players(message):
    user_id = message.from_user.id
    try:
        number_of_players = int(message.text)
    except ValueError:
        mafia_bot.send_message(user_id, ERROR_NUMBER_MESSAGE)
        mafia_bot.register_next_step_handler(message, handle_players)
    else:
        if number_of_players < 3:
            mafia_bot.send_message(user_id, 'игроков должно быть больше 3')
            mafia_bot.register_next_step_handler(message, handle_players)
        else:
            room_code = randint(100000, 999999) if not DEBUG else DEBUG_ROOM_CODE
            while room_code in rooms.keys():  # генерируем номер для случайной комнаты
                room_code = randint(100000, 999999)
            players_room[message.from_user.id] = room_code
            roles = ROLES[:]
            configure_roles(number_of_players, roles)
            rooms[room_code] = {
                'master_id': user_id,  # необходимо чтобы потом слать ведущему сообщения
                'count_for_play': number_of_players,
                'players': get_mock_players() if DEBUG else [],  # debugging
                'roles': roles,
                'dependent_players': [],
                'ready_for_play': False,
                'game_is_started': False,
                'game_is_finished': False,
                'queue': 0,
                'time': 'night',
            }
            mafia_bot.send_message(user_id, f'Комната с номером `{room_code}` создана,'
                                            'поделитесь этим номером с игроками')
            # ждем других игроков
            room = rooms[room_code]  # наша комната
            while len(room['players']) < room['count_for_play']:
                sleep(1)
            players_name = [player.name for player in room['players']]
            mafia_bot.send_message(user_id, f'Игроки собрались: {", ".join(players_name)}')
            mafia_bot.send_message(user_id, 'Раздаем роли')
            set_roles(room['players'], room['roles'])
            mafia_bot.send_message(user_id, 'Роли розданы:')
            # рассылаем всем роли
            for player in room['players']:
                mafia_bot.send_message(user_id, f'{player.name}: {player.role}')
                with open(f'images/{player.role}.png', 'rb') as img:
                    mafia_bot.send_photo(player.id, img)
                mafia_bot.send_message(player.id, f'Вы {player.role}')

            # игра
            for player in room['players']:
                mafia_bot.send_message(player.id, 'Наступает ночь, город засыпает...')
            keyboard = types.InlineKeyboardMarkup()
            go_button = types.InlineKeyboardButton(text='Начать игру!', callback_data='night')
            keyboard.add(go_button)
            mafia_bot.register_next_step_handler(message, handle_night)

            # room['game_is_started'] = True

            # snapshot_of_players_status = get_players_status(rooms[room_code]['players'])
            # очищаем комнату в конце игры
            while not rooms[room_code]['game_is_finished']:
                sleep(1)
            del rooms[room_code]


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
    # if len(room['players']) >= room['count_for_play']:
    #     room['ready_for_play'] = True
    #
    # while not room['game_is_started']:
    #     sleep(1)
    # mafia_bot.send_message(user_id, 'Начинаем игру!!!')
    # handle_game(message, player)


@mafia_bot.callback_query_handler(lambda call: players_room.get(call.from_user.id) and call.data == 'night')
def handle_night(message):
    room_code = players_room[message.from_user.id]
    room = rooms[room_code]
    alive_players = [player for player in room['players'] if player.is_alive]
    for player in alive_players:
        mafia_bot.send_message(player.id, 'Наступает ночь, город засыпает...')  # можно картиночку послать ночи

    for role in room['roles']:
        for player in alive_players:
            mafia_bot.send_message(player.id, f'Ходит {role}')  # можно картиночку послать ночи

        players_with_role = list(filter(lambda player: player.role == role, room['players']))
        for player in players_with_role:
            keyboard = return_keyboard_with_alive_players(room['players'], player)
            mafia_bot.send_message(player.id, f'Ходит {role}')

    # игра ночью
    while player.role != room['roles'][room['queue']] and not DEBUG:
        sleep(1)
    if player.role != 'civilian':
        keyboard = return_keyboard_with_alive_players(room['players'], player)
        action_message = ''
        match player.role:
            case 'mafia':
                action_message = 'выберете кого убить...'
            case 'doctor':
                action_message = 'выберете кого спасти...'
            case 'sherif':
                action_message = 'выберете кого арестовать...'
        mafia_bot.send_message(player.id, action_message, reply_markup=keyboard)

    # while room['time'] != 'day':
    #     sleep(1)
    #
    # mafia_bot.register_next_step_handler(message, handle_game)


def check_list_names(call):
    return players_room.get(call.from_user.id) and \
        int(call.data) in [player.id for player in rooms[players_room[call.from_user.id]]['players']]


@mafia_bot.callback_query_handler(check_list_names)
def player_action(call):
    player = get_player_through_players_room(call.from_user.id)
    room = rooms[player.room_code]
    match player.role:
        case 'mafia':
            dependent_player = get_player_through_id(room['players'], int(call.data))
            dependent_player.is_alive = False
            room['dependent_players'].append(dependent_player)
        case 'sherif':
            dependent_player = get_player_through_id(room['players'], int(call.data))
            room['dependent_players'].append(dependent_player)
        case 'doctor':
            dependent_player = get_player_through_id(room['players'], int(call.data))
            dependent_player.is_alive = True
            room['dependent_players'].append(dependent_player)
    end_queue = len(room['roles']) - 1
    if room['queue'] < end_queue:
        room['queue'] += 1
    else:
        room['queue'] = 0
        room['time'] = 'day'
        mafia_bot.send_message(player.id, 'Наступает день... город просыпается')
        # mafia_bot.register_next_step_handler(call.message, handle_day)


    mafia_bot.register_next_step_handler(call.message, handle_night)

    # mafia_bot.send_message(user_id, 'Наступает день, город просыпается...')
    # # проверяем результаты
    # is_end, message_for_user = check_end_game_condition_and_return_bool_and_message(rooms[room_code]['players'])
    # if not is_end:
    #     mafia_bot.send_message(user_id, message_for_user)
    #     handle_game(message, user_id, room_code)
    # # если конец игры
    # mafia_bot.send_message(user_id, 'Спасибо за игру!!!')
    # rooms[room_code]['game_is_finished'] = True


def get_player_through_players_room(user_id) -> Player:
    room_code = players_room[user_id]
    all_players = rooms[room_code]['players']
    for i in range(len(all_players)):
        if all_players[i].id == user_id:
            return all_players[i]


if __name__ == '__main__':
    mafia_bot.polling(none_stop=True, interval=0)
