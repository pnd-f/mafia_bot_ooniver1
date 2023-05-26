from time import sleep
from random import randint

from telebot import TeleBot, types

from settings import HELLO_MESSAGE, BOT_TOKEN, DEBUG, ROLES
from model import Player
from player_factory import get_mock_players
from utils import set_roles, get_players_status, check_end_game_condition_and_return_bool_and_message, \
    get_player_for_queue, configure_roles

mafia_bot = TeleBot(BOT_TOKEN)

players_room = {}  # используется для хранения номера комнаты
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


@mafia_bot.callback_query_handler(lambda call: True)
def play(call):
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
def help(message):
    match message.text:
        case '/help':
            mafia_bot.send_message(message.from_user.id, HELLO_MESSAGE)
        case _:
            mafia_bot.send_message(message.from_user.id, 'чтобы понять, как пользоваться ботом напиши `/help`')


def handle_players(message):
    user_id = message.from_user.id
    try:
        number_of_players = int(message.text)
    except ValueError as e:
        mafia_bot.send_message(user_id, 'Ошибка!!! Введите число!!')
        mafia_bot.register_next_step_handler(message, handle_players)
    if number_of_players < 3:
        mafia_bot.send_message(user_id, 'игроков должно быть больше 3')
        mafia_bot.register_next_step_handler(message, handle_players)
    else:
        room_code = randint(100000, 999999)
        while room_code in rooms.keys():  # генерируем номер для случайной комнаты
            room_code = randint(100000, 999999)
        configure_roles(number_of_players)
        rooms[room_code] = {
            'master_id': user_id,  # необходимо чтобы потом слать ведущему сообщения
            'count_for_play': number_of_players,
            'players': get_mock_players() if DEBUG else [],  # debugging
            'ready_for_play': False,
            'game_is_started': False,
            'game_is_finished': False,
            'time': 'day',
        }
        mafia_bot.send_message(user_id, f'Комната с номером `{room_code}` создана,'
                                        'поделитесь этим номером с игроками')
        # ждем других игроков
        while not rooms[room_code]['ready_for_play']:
            sleep(1)
        players_name = [player.name for player in rooms[room_code]['players']]
        mafia_bot.send_message(user_id, f'Игроки собрались: {", ".join(players_name)}')
        mafia_bot.send_message(user_id, 'Раздаем роли')
        set_roles(rooms[room_code]['players'])
        mafia_bot.send_message(user_id, 'Роли розданы:')
        # рассылаем всем роли
        for player in rooms[room_code]['players']:
            mafia_bot.send_message(user_id, f'{player.name}: {player.role}')
            with open(f'images/{player.role}.png', 'rb') as img:
                mafia_bot.send_photo(player.id, img)
            mafia_bot.send_message(player.id, f'Вы {player.role}')

        # игра
        rooms[room_code]['game_is_started'] = True
        # snapshot_of_players_status = get_players_status(rooms[room_code]['players'])
        # очищаем комнату
        while not rooms[room_code]['game_is_finished']:
            sleep(1)
        del rooms[room_code]


def handle_code(message):
    user_id = message.from_user.id
    room_code = int(message.text)
    if room_code not in rooms.keys():
        mafia_bot.send_message(user_id, f'Комнаты {room_code} не существует! попробуйте еще раз')
    else:
        player = Player(user_id, room_code)
        players_room[
            user_id] = room_code  # помещаем комнаты для юзера, чтобы пробросить в следующую функцию
        rooms[room_code]['players'].append(player)
        mafia_bot.send_message(user_id, f'Введите своё имя')
        mafia_bot.register_next_step_handler(message, handle_name)


def handle_name(message):
    user_id = message.from_user.id
    name = message.text
    player = get_player_through_message(message)
    player.name = name
    room_code = players_room[user_id]
    mafia_bot.send_message(user_id, f'Ждём других игроков...')
    if len(rooms[room_code]['players']) >= rooms[room_code]['count_for_play']:
        rooms[room_code]['ready_for_play'] = True

    while not rooms[room_code]['game_is_started']:
        sleep(1)
    mafia_bot.send_message(user_id, 'Начинаем игру!!!')

    queue_order = 0
    handle_game(message, user_id, room_code, queue_order)


def handle_game(message, user_id, room_code, queue_order):
    mafia_bot.send_message(user_id, 'Наступает ночь, город засыпает...')
    # игра ночью
    role = ROLES[queue_order]
    pass  # TODO игроки ходят по очереди, сделать им кнопки
    if not role == 'civilian':
        player = get_player_for_queue(rooms[room_code]['players'], role)
        # TODO выполнить ход
    mafia_bot.send_message(user_id, 'Наступает день, город просыпается...')
    # проверяем результаты
    is_end, message_for_user = check_end_game_condition_and_return_bool_and_message(rooms[room_code]['players'])
    if not is_end:
        mafia_bot.send_message(user_id, message_for_user)
        handle_game(message, user_id, room_code)
    # если конец игры
    mafia_bot.send_message(user_id, 'Спасибо за игру!!!')
    rooms[room_code]['game_is_finished'] = True


def get_player_through_message(message):
    user_id = message.from_user.id
    room_code = players_room[user_id]
    all_players = rooms[room_code]['players']
    for i in range(len(all_players)):
        if all_players[i].id == user_id:
            return all_players[i]


if __name__ == '__main__':
    mafia_bot.polling(none_stop=True, interval=0)
