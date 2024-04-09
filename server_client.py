class ServerClient:
    def __init__(self, socket, ip, nickname):
        self.socket = socket
        self.address = ip
        self.nickname = nickname

    def get_nickname(self):
        return self.nickname

    def get_address(self):
        return self.address
    
    def get_socket(self):
        return self.socket

    def get_self(self):
        return self
    
    def set_nickname(self,new_nick):
        self.nickname = new_nick
