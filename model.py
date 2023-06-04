from random import randint


class Player:
    def __init__(self, user_id, name, room_code):
        self.id = user_id
        self.name = name
        self.room_code = room_code
        self.role = None
        self.is_alive = True

    def __repr__(self):
        return f'{self.name} - {self.role if self.role else ""}'


class Room:
    def __init__(self, master_id, quantity_of_players, roles):
        self.master_id = master_id  # необходимо чтобы потом слать ведущему сообщения
        self.quantity_of_players = quantity_of_players
        self.players = []  # здесь будут храниться наши пришедшие игроки
        self.roles = roles  # роли для игроков
        self.players_fate = {}  # специальный объект который хранит выбор игроков когда они походили
        self.queue = 0,  # очередь хода игрока, привязана к ролям, изменяется ночью
        self.open = True  # открыта ли комната для игроков

    def set_roles(self):
        used_index = []
        _roles = self.roles[:]
        while len(_roles) != 0:
            role = _roles.pop(0)
            rand_index = randint(0, len(self.players) - 1)
            while rand_index in used_index:
                rand_index = randint(0, len(self.players) - 1)
            self.players[rand_index].role = role
            used_index.append(rand_index)
        for i in range(len(self.players)):
            if i in used_index:
                continue
            self.players[i].role = 'Мирные жители'

    def get_alive_players(self):
        return [player for player in self.players if player.is_alive]

    def get_players_with_role(self, role: str):
        return list(filter(lambda player: player.role == role and player.is_alive, self.players))

    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

    def check_end_game_condition_after_night_and_return_bool_and_message(self):
        """
        Нужно каждый день, после ночи проверять, закончилась ли игра.
        Игра заканчивается либо когда мафию словили, либо когда убили всех мирных граждан
        :param room:
        :return: bool, str
        """
        end_game = False
        mafia_players = self.get_players_with_role('Мафия')
        killed_players = self.players_fate['Мафия']
        arrested_players = self.players_fate.get('Шериф', [])
        saved_players = self.players_fate.get('Доктор', [])

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
        mafia = self.get_players_with_role('Мафия')
        civilians = self.get_players_with_role('Мирные жители')
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
        # проверяем остались ли доктора и шерифы, если нет,
        # убираем их роли из списка ролей комнаты
        sheriffs = self.get_players_with_role('Шериф')
        doctors = self.get_players_with_role('Доктор')
        if len(sheriffs) == 0:
            for i in range(len(self.roles)):
                if self.roles[i] == 'Шериф':
                    del self.roles[i]
        if len(doctors) == 0:
            for i in range(len(self.roles)):
                if self.roles[i] == 'Доктор':
                    del self.roles[i]

        # очищаем выбор игроков для следующего хода
        self.players_fate = {}
        return end_game, message
