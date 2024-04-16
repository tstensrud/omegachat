from typing import List
class Channel:
    def __init__(self, name: str, motd: str):
        self.name = name
        self.motd = motd
        self.active_users = UserList(name) # each channel has own UserList() object
        self.operators = []

    def get_name(self) -> str:
        return self.name
    def get_motd(self) -> str:
        return self.motd
    def set_operator(self, nickname):
        operator = self.active_users.get_user(nickname)
        if operator == "Not found":
            return
        else:
            self.operators.append(operator)

    def get_operators(self) -> List[str]:
        return self.operators

    def get_active_users(self) -> List[str]:
        return self.active_users

class UserList:
    def __init__(self, channel_name: str):
        self.users = []
        self.count = 0
        self.name = channel_name

    def update_user_count(self) -> None:
        self.count = len(self.users)
    def add_user(self, user: str) -> None:
        self.users.append(user)
        self.users.sort()
        self.count += 1
    def remove_user(self, username: str) -> None:
        self.users.pop(self.users.index(username))
        self.users.sort()
        self.count -= 1

    def get_users(self) -> List[str]:
        return self.users

    def get_user(self, username) -> str:
        for user in self.users:
            if user == username:
                return user
        return "Not found"
    def get_user_count(self) -> int:
        return self.count
