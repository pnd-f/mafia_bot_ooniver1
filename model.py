class Player:
    def __init__(self, user_id, name, room_code):
        self.id = user_id
        self.name = name
        self.room_code = room_code
        self.role = None
        self.is_alive = True

    def __repr__(self):
        return f'{self.name} - {self.role if self.role else ""}'
