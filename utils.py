
from random import randint
from const import ROLES


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
