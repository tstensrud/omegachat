import socket

class Client:
    def __init__(self, HOST, PORT, client, nickname):
        self.HOST = "127.0.0.1"
        self.PORT = 55555
        self.encoding = "ascii"
        self.client = None
        self.nickname = None

    def login(self, name):
        self.nickname = name
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.HOST, self.PORT))
            print("Connected")
            message = self.client.recv(1024).decode(self.encoding)
            if message == "NICK":
                self.client.send(f"{self.nickname}".encode(self.encoding))
                message = self.client.recv(1024).decode(self.encoding)
                if message == "Err-1":
                    print("Nick not unique")
                    self.client.close()
                    return message
                print("Nick accepted")
            

        except Exception as e:
            print(f"Connection-error: {e}")


    def write(self, input):
        message = f"{self.nickname}: {input}"
        self.client.send(message.encode(self.encoding))


    def disconnect(self):
        self.client.close()