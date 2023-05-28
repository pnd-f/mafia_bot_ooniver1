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
        players[i].role = 'Мирные граждане'


def get_players_status(players):
    statuses = {}
    for player in players:
        statuses[player.name] = 'alive' if player.is_alive else 'dead'
    return statuses




def check_end_game_condition_and_return_bool_and_message(players: [Player]):
    """
    Нужно каждый ход проверять, закончилась ли игра.
    Игра заканчивается либо когда мафию словили, либо когда убили шерифа или всех мирных граждан
    :param players:
    :return: bool, str
    """
    mafia_is_alive = [player.is_alive for player in players if player.role == 'mafia'][0]
    sherif_is_alive = [player.is_alive for player in players if player.role == 'sherif'][0]
    civilians_status = [player.is_alive for player in players if player.role == 'civilian']
    message = 'игра продолжается'
    end_game = False
    if not mafia_is_alive:
        end_game = True
        message = 'мафию словили!!!'
    if not sherif_is_alive:
        end_game = True
        message = 'шериф был убит...'
    civilian_alive_count = 0
    for status in civilians_status:
        if status:
            civilian_alive_count += 1
    if civilian_alive_count == 0:
        end_game = True
        message = 'все мирные жители убиты...'

    return end_game, message


def return_keyboard_with_alive_players(players, exclude_player):
    keyboard = types.InlineKeyboardMarkup()
    buttons = []
    for player in players:
        if player.name != exclude_player.name and player.is_alive:
            buttons.append(types.InlineKeyboardButton(text=player.name, callback_data=player.id))
    keyboard.add(*buttons)
    return keyboard


def get_player_through_id(players, user_id):
    for player in players:
        if player.id == user_id:
            return player
