class Player:
    def __init__(self, user_id, code_room):
        self.id = user_id
        self.name = ''
        self.code_room = code_room
        self.role = None
        self.is_alive = True

    def __repr__(self):
        return self.name if self.name else 'anonim'
