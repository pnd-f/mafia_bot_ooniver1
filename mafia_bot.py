from random import randint
import os

from telebot import TeleBot, types

from settings import HELLO_MESSAGE, BOT_TOKEN, ROLES, ERROR_NUMBER_MESSAGE, FILE_NAMES
from model import Player, Room
from utils import configure_roles, return_keyboard_with_alive_players

mafia_bot = TeleBot(BOT_TOKEN)

players_room: dict[int, int] = {}  # используется для хранения номера комнаты для пользователя
rooms: dict[int, Room] = {}  # комнаты


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
    match call.data:
        case 'ведущий':
            mafia_bot.send_message(user_id, 'Приветствую тебя, Ведущий!')

            mafia_bot.send_message(
                user_id,
                'Игроков должно быть не меньше трех: \n'
                '- Мафия\n'
                '- Шериф\n'
                '- Мирные жители\n'
                'Если игроков будет больше - добавим доктора.\n'
                'Сколько будет игроков?'
            )
            mafia_bot.register_next_step_handler(call.message, handle_players)
        case 'игрок':
            mafia_bot.send_message(user_id, 'Введите номер комнаты, чтобы присоединиться')
            mafia_bot.register_next_step_handler(call.message, handle_code)


@mafia_bot.callback_query_handler(
    lambda call: players_room.get(call.from_user.id) and (call.data == 'ведущий' or call.data == 'игрок'))
def check_again_master_or_player(call):
    user_id = call.from_user.id
    room_code = players_room[user_id]
    room = rooms[room_code]
    if user_id == room.master_id:
        mafia_bot.send_message(user_id, f'Вы уже состоите как ведущий в комнате {room_code}...')
    else:
        mafia_bot.send_message(user_id, f'Вы уже состоите как игрок в комнате {room_code}...')


@mafia_bot.message_handler(content_types=['text'])
def help_message(message):
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
            mafia_bot.send_message(user_id, 'игроков должно быть больше 3, попробуйте еще раз')
            mafia_bot.register_next_step_handler(message, handle_players)
        else:
            # генерируем номер для случайной комнаты
            # пока он не будет уникальный
            while (room_code := randint(100, 999)) in rooms.keys():
                pass
            players_room[message.from_user.id] = room_code  # комната ведущего
            roles = ROLES[:]
            configure_roles(quantity_of_players, roles)
            room = Room(user_id, quantity_of_players, roles)
            rooms[room_code] = room
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
            mafia_bot.send_message(
                user_id, f'Комнаты {room_code} не существует! Чтобы попробовать еще раз, войдите как игрок заново')
        elif not rooms[room_code].open:
            mafia_bot.send_message(user_id, f'В комнате {room_code} игроки уже собрались, выберите другую')
            mafia_bot.register_next_step_handler(message, handle_code)
        else:
            players_room[user_id] = room_code  # назначаем игроку комнату
            mafia_bot.send_message(user_id, f'Приветствую тебя, игрок!')
            mafia_bot.send_message(user_id, f'Как тебя зовут?')
            mafia_bot.register_next_step_handler(message, handle_name)


def handle_name(message):
    user_id = message.from_user.id
    room_code = players_room[user_id]  # забираем номер комнаты для игрока
    name = message.text
    player = Player(user_id, name, room_code)
    room = rooms[room_code]
    room.players.append(player)
    mafia_bot.send_message(user_id, f'Ждём других игроков...')
    if len(room.players) >= room.quantity_of_players:
        # закрываем комнату для новых игроков
        room.open = False
        # говорим ведущему, что все в сборе
        master_id = room.master_id
        players_name = [player.name for player in room.players]
        mafia_bot.send_message(master_id, f'Игроки собрались: {", ".join(players_name)}')
        mafia_bot.send_message(master_id, 'Раздаем роли')
        # назначаем роли
        room.set_roles()
        # рассылаем роли мастеру и всем игрокам
        mafia_bot.send_message(master_id, 'Роли розданы:')
        for player in room.players:
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
    alive_players = room.get_alive_players()

    role = room.roles[room.queue]
    for player in alive_players:
        mafia_bot.send_message(player.id, f'Ходит {role}')  # можно картиночку послать ночи

    players_with_role = room.get_players_with_role(role)
    action_message = {
        'Мафия': 'выберете кого убить...',
        'Доктор': 'выберете кого спасти...',
        'Шериф': 'выберете кого арестовать...'
    }

    for player in players_with_role:
        keyboard = return_keyboard_with_alive_players(room.players, player)
        mafia_bot.send_message(player.id, action_message[role], reply_markup=keyboard)


def check_night_action(call):
    user_id = call.from_user.id
    room_code = players_room.get(user_id)
    if room_code:
        room = rooms[room_code]
        player = room.get_player_by_id(user_id)
        return not player.pressed_button and \
            room.time == 'night' and \
            call.data != 'day' and call.data != 'night' and call.data != 'ведущий' and call.data != 'игрок' and \
            call.data != 'day_results' and \
            int(call.data) in [player.id for player in room.get_alive_players()]

    else:
        return False
    

@mafia_bot.callback_query_handler(check_night_action)
def night_action(call):
    room_code = players_room[call.from_user.id]
    room = rooms[room_code]
    player = room.get_player_by_id(call.from_user.id)

    selected_player = room.get_player_by_id(int(call.data))
    if player.role in room.players_fate:
        room.players_fate[player.role].append(selected_player)
    else:
        room.players_fate[player.role] = [selected_player]
    player.pressed_button = True

    if room.queue < len(room.roles) - 1:
        room.queue += 1
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Передать ход', callback_data='night')
        keyboard.add(next_button)
        mafia_bot.send_message(player.id, f'Вы выбрали {selected_player.name}', reply_markup=keyboard)
    else:
        mafia_bot.send_message(player.id, f'Вы выбрали {selected_player.name}...')
        room.queue = 0

        for each_player in room.get_alive_players():
            mafia_bot.send_message(each_player.id, 'Наступает день... город просыпается')
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Дождаться утра', callback_data='day')
        keyboard.add(next_button)
        mafia_bot.send_message(room.master_id, 'Наступает день... город просыпается', reply_markup=keyboard)
        room.time = 'day'
        for i in range(len(room.players)):
            room.players[i].pressed_button = False


@mafia_bot.callback_query_handler(lambda call: players_room.get(call.from_user.id) and call.data == 'day')
def handle_day(call):
    room_code = players_room[call.from_user.id]
    room = rooms[room_code]
    end_game, message = room.check_end_game_condition_after_night_and_return_bool_and_message()

    mafia_bot.send_message(room.master_id, message)  # отдельно шлем мастеру
    for player in room.players:
        mafia_bot.send_message(player.id, message)
    if not end_game:
        # Этап голосования всех живых игроков
        alive_players = room.get_alive_players()
        for player in alive_players:
            keyboard = return_keyboard_with_alive_players(room.players, player)
            mafia_bot.send_message(player.id, 'Как вы думаете, кто мафия?', reply_markup=keyboard)
    else:  # заканчиваем игру
        for player in room.players:
            mafia_bot.send_message(player.id, 'Игра закончена. Спасибо за игру!!!')
        mafia_bot.send_message(room.master_id, 'Игра закончена. Спасибо за игру!!!')  # отдельно шлем мастеру
        clear_room(room_code)


def check_day_action(call):
    user_id = call.from_user.id
    room_code = players_room.get(user_id)
    if room_code:
        room = rooms[room_code]
        player = room.get_player_by_id(user_id)
        return not player.pressed_button and \
            room.time == 'day' and \
            call.data != 'day' and call.data != 'night' and call.data != 'ведущий' and call.data != 'игрок' and \
            call.data != 'day_results' and \
            int(call.data) in [player.id for player in room.get_alive_players()]
    else:
        return False


@mafia_bot.callback_query_handler(check_day_action)
def day_action(call):
    user_id = call.from_user.id
    room_code = players_room[user_id]
    room = rooms[room_code]
    player = room.get_player_by_id(user_id)
    selected_player = room.get_player_by_id(int(call.data))
    if selected_player.id in room.players_fate:
        room.players_fate[selected_player.id] += 1
    else:
        room.players_fate[selected_player.id] = 1
    player.pressed_button = True

    mafia_bot.send_message(player.id, f'Вы выбрали {selected_player.name}...')
    # считаем количество проголосовавших,
    quantity = 0
    for _, value in room.players_fate.items():
        quantity += value
    # если проголосовали все, ведущему даем кнопку "узнать результаты"
    if quantity == len(room.get_alive_players()):
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Показать результаты голосования', callback_data='day_results')
        keyboard.add(next_button)
        mafia_bot.send_message(room.master_id, 'Все проголосовали', reply_markup=keyboard)


@mafia_bot.callback_query_handler(lambda call: players_room.get(call.from_user.id) and call.data == 'day_results')
def handle_in_afternoon(call):
    user_id = call.from_user.id
    room_code = players_room[user_id]
    room = rooms[room_code]
    end_game, message = room.check_end_game_condition_after_day_and_return_bool_and_message()
    if not end_game:
        mafia_bot.send_message(room.master_id, message)
        for player in room.players:
            mafia_bot.send_message(player.id, message)
            mafia_bot.send_message(player.id, 'Наступает ночь, город засыпает...')
        keyboard = types.InlineKeyboardMarkup()
        next_button = types.InlineKeyboardButton(text='Продолжить!', callback_data='night')
        keyboard.add(next_button)
        mafia_bot.send_message(room.master_id, 'Наступает ночь, город засыпает...', reply_markup=keyboard)
        for i in range(len(room.players)):
            room.players[i].pressed_button = False

    else:  # заканчиваем игру
        for player in room.players:
            mafia_bot.send_message(player.id, 'Игра закончена. Спасибо за игру!!!')
        mafia_bot.send_message(room.master_id, 'Игра закончена. Спасибо за игру!!!')  # отдельно шлем мастеру
        clear_room(room_code)


@mafia_bot.message_handler(commands=['clear'])
def master_cleans_room(message):
    master_id = message.from_user.id
    if room_code := players_room.get(master_id):
        room = rooms[room_code]
        if message.text == '/clear':
            if master_id == room.master_id:
                for player in room.players:
                    mafia_bot.send_message(player.id, 'Ведущий удаляет вашу комнату')
                clear_room(room_code)
        mafia_bot.send_message(master_id, f'Комната {room_code} удалена')

    else:
        mafia_bot.send_message(master_id, 'Вы не состоите ни в какой комнате')


def clear_room(room_code):
    room = rooms[room_code]
    # очищаем пользователей
    for player in room.players:
        del players_room[player.id]
    del players_room[room.master_id]  # очищаем мастера
    del rooms[room_code]  # удаляем комнату


if __name__ == '__main__':
    mafia_bot.polling(none_stop=True, interval=0)
