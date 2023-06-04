from telebot import types


def configure_roles(number_of_players, roles):
    if number_of_players > 3:
        roles.append('Доктор')


def return_keyboard_with_alive_players(players, exclude_player):
    keyboard = types.InlineKeyboardMarkup()
    buttons = []
    for player in players:
        if player.id != exclude_player.id and player.is_alive:
            buttons.append(types.InlineKeyboardButton(text=player.name, callback_data=player.id))
    keyboard.add(*buttons)
    return keyboard
