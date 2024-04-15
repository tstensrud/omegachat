class Message:
    def __init__(self, id: str, date: str, owner: str, message):
        self.id = id # "msg" if regular chatmsg. "add_nick" and "remove_nick" when connecting and disconnecting
        self.date = date
        self.owner = owner
        self.message = message




