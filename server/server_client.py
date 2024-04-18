from typing import List

class ServerClient:
    def __init__(self, socket, ip, nickname):
        self.socket = socket
        self.address = ip
        self.nickname = nickname
        self.channels = []

    def get_nickname(self) -> str:
        return self.nickname

    def get_address(self) -> str:
        return self.address
    
    def get_socket(self):
        return self.socket
    
    def set_nickname(self, new_nick: str) -> None:
        self.nickname = new_nick

    def add_channel(self, channel: str) -> None:
        self.channels.append(channel)

    def get_channels(self) -> List[str]:
        return self.channels

    def remove_channel(self, channel_name):
        self.channels.pop(self.channels.index(channel_name))