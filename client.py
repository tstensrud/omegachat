import socket
import threading
from gui import Omegachat

def main():
    window = Omegachat()
    window.mainloop()

HOST = "127.0.0.1"
PORT = 55555

encoding = "ascii"
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

nickname = input("Choose a nickname: ")

def receive():
    while True:
        try:
            message = client.recv(1024).decode(encoding)
            if message == "NICK":
                client.send(nickname.encode(encoding))
            else:
                print(message)
        except:
            print("Error")
            client.close()
            break

def write():
    while True:
        message = f"{nickname}: {input('')}"
        client.send(message.encode(encoding))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

if __name__ == "__main__":
    main()
