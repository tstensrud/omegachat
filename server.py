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
nicknames = ["name"]
# date = datetime.datetime.now().strftime("%H:%M:%S")

def find_nick_name(name):
    for nickname in nicknames:
        if nickname == name:
            return True
    return False

def broadcast(message):
    for client in clients:
        client.send(f"{message}".encode(encoding))

def handle(client):
    while True:
        try:
            date = datetime.datetime.now().strftime("[%H:%M:%S]")
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

def client_connection():
    while True:
        client, address = server.accept()
        print(f"Connected {str(address)}")
        client.send("NICK".encode(encoding))
        nickname = client.recv(1024).decode(encoding)
        if find_nick_name(nickname):
            client.send("Err-1".encode(encoding))
        else: 
            nicknames.append(nickname)
            clients.append(client)
            broadcast(f"{nickname} joined the chat.")
            client.send("Connected to the server".encode(encoding))

            thread = threading.Thread(target=handle, args=(client,))
            thread.daemon = True
            thread.start()

print("Server is running")
client_connection()