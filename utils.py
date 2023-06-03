from random import randint

from telebot import types

from model import Player


def configure_roles(number_of_players, roles):
    if number_of_players > 3:
        roles.append('Доктор')


def set_roles(players, roles):
    used_index = []
    _roles = roles[:]
    while len(_roles) != 0:
        role = _roles.pop(0)
        rand_index = randint(0, len(players) - 1)
        while rand_index in used_index:
            rand_index = randint(0, len(players) - 1)
        players[rand_index].role = role
        used_index.append(rand_index)
    for i in range(len(players)):
        if i in used_index:
            continue
        players[i].role = 'Мирные жители'


def check_end_game_condition_after_night_and_return_bool_and_message(room):
    """
    Нужно каждый день, после ночи проверять, закончилась ли игра.
    Игра заканчивается либо когда мафию словили, либо когда убили всех мирных граждан
    :param room:
    :return: bool, str
    """
    end_game = False
    players_fate = room.players_fate
    mafia_players = [player for player in room.players if player.role == 'Мафия' and player.is_alive is True]
    killed_players = players_fate['Мафия']
    arrested_players = players_fate.get('Шериф', [])
    saved_players = players_fate.get('Доктор', [])

    message = ''
    for player in arrested_players:
        if player in mafia_players:
            if player in saved_players:
                message += f'Игрок мафии {player.name} был ранен шерифом, но спасен доктором!\n'
            else:
                player.is_alive = False
                message += f'Игрок мафии {player.name} был застрелен шерифом!\n'
        else:
            message += 'Шериф арестовал не того...\n'

    for player in killed_players:
        if player in saved_players:
            message += f'Игрок {player.name} - был ранен мафией, но спасен доктором\n'
        else:
            message += f'Игрок {player.role} - {player.name} - был убит мафией\n'
            player.is_alive = False

    # cчитаем сколько осталось в живых мафии и мирных жителей
    mafia = [player for player in room.players if player.role == 'Мафия' and player.is_alive]
    civilians = [player for player in room.players if player.role == 'Мирные жители' and player.is_alive]
    # если шериф поймал всю мафию, игра заканчивается
    if not len(mafia):
        end_game = True
        message += 'Мафии больше не осталось\n'
    # если мирных жителей не осталось, мафия победила
    elif not len(civilians):
        end_game = True
        message += 'Мирных жителей больше не осталось, мафия побеждает\n'
    else:
        message += 'Игра продолжается\n'

    # очищаем выбор игроков для следующего хода
    room.players_fate = {}
    return end_game, message


def return_keyboard_with_alive_players(players, exclude_player):
    keyboard = types.InlineKeyboardMarkup()
    buttons = []
    for player in players:
        if player.name != exclude_player.name and player.is_alive:
            buttons.append(types.InlineKeyboardButton(text=player.name, callback_data=player.id))
    keyboard.add(*buttons)
    return keyboard


def get_player_through_id(players, user_id) -> Player:
    for player in players:
        if player.id == user_id:
            return player
