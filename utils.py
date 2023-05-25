from random import randint
from const import ROLES
from model import Player


def set_roles(players):
    used_index = []
    if len(players) > 3:
        ROLES.append('doctor')

    while len(ROLES) != 0:
        role = ROLES.pop(0)
        rand_index = randint(0, len(players) - 1)
        while rand_index in used_index:
            rand_index = randint(0, len(players) - 1)
        players[rand_index].role = role
        used_index.append(rand_index)
    for i in range(len(players)):
        if i in used_index:
            continue
        players[i].role = 'civilian'


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
