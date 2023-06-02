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
        self.players_fate: {}  # специальный объект который хранит выбор игроков когда они походили
        self.queue = 0,  # очередь хода игрока, привязана к ролям, изменяется ночью
        self.open = True  # открыта ли комната для игроков
