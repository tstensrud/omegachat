from typing import List
class Channel:
    def __init__(self, name: str, motd: str):
        self.name = name
        self.motd = motd
        self.active_users = []
        self.operators = []

    def get_name(self) -> str:
        return self.name
    def get_motd(self) -> str:
        return self.motd
    def get_operators(self) -> List[str]:
        return self.operators

    def get_active_users(self) -> List[str]:
        return self.active_users
