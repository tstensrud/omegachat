import socket
import threading
import datetime


HOST = "127.0.0.1"
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

encoding = "ascii"

clients = []
nicknames = []
# date = datetime.datetime.now().strftime("%H:%M:%S")
def broadcast(message):
    for client in clients:
        client.send(f"{message}".encode(encoding))

def handle(client):
    while True:
        try:
            date = datetime.datetime.now().strftime("%H:%M:%S")
            message = client.recv(1024).decode(encoding)
            broadcast(f"{date} {message}")
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f"{nickname} left the chat".encode(encoding))
            nicknames.remove(nickname)
            break

def receive():
    while True:
        client, address = server.accept()
        print(f"Connected {str(address)}")

        client.send("NICK".encode(encoding))
        nickname = client.recv(1024).decode(encoding)
        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname of client is {nickname}.")
        broadcast(f"{nickname} joined the chat.".encode(encoding))
        client.send("Connected to the server".encode(encoding))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Server is running")
receive()

