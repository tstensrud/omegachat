import socket
import sys
import threading
import datetime
import tkinter as tk
from tkinter import scrolledtext

class OmegachatServer:
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 55555
        self.server = None
        self.encoding = "ascii"
        self.clients = []
        self.nicknames = ["name"]
        self.all_clients = {"name" : "123.456.789"}

        self.root = tk.Tk()
        self.root.title("Omegachat - SERVER")
        self.root.config(background="black")
        self.root.geometry("1024x768")

        self.main_frame = tk.Frame(self.root, bg="black")
        self.main_frame.bind("<Configure>", self.frame_resizing)
        self.main_frame.pack(expand=True, fill="both")


        self.output = scrolledtext.ScrolledText(self.main_frame, bg="black", fg="white")
        self.output.pack(expand=True, fill="both")

        self.menu_bar = tk.Menu(self.root)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Start server", command=self.start_server)
        self.options_menu.add_command(label="Stop server", command=self.stop_server)
        self.options_menu.add_command(label="Exit", command=self.exit)
        self.menu_bar.add_cascade(label="Server options", menu=self.options_menu)
        self.users_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.users_menu.add_command(label="List users", command=self.list_connected_users)
        self.menu_bar.add_cascade(label="User options", menu=self.users_menu)
        
        self.root.config(menu=self.menu_bar)
        self.root.mainloop()
        

    def frame_resizing(self, event):
        self.main_frame.config(width=event.width)
    
    def date(self):
        return datetime.datetime.now().strftime("[%Y-%M-%d %H:%M:%S]")

    def server_message(self, message, date):
        if date == True:
            self.output.insert(tk.END, f"{self.date()}: {message}\n")
        else:
            self.output.insert(tk.END, f"{message}\n")
        self.output.yview(tk.END)

    # start server and thread for accepting new clients
    def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.HOST, self.PORT))
        self.server.listen()
        
        client_thread = threading.Thread(target=self.client_connection)
        client_thread.start()
    
    # stop server
    def stop_server(self):
        self.server_message(f"Stopped server", True)

    # exit server-program
    def exit(self):
        sys.exit()

    # find nickname. return True if found
    def find_nick_name(self, name):
        for nickname in self.nicknames:
            if nickname == name:
                return True
        return False

    # list all connected users
    def list_connected_users(self):
        self.server_message("Connected users nicknames and IPs:")
        for key,value in self.all_clients.items():
            print(f"{key}: {value}")
            self.server_message(f"{key}: {value}", False)
    
    # broadcast message to all connected users
    def broadcast(self, message):
        for client in self.clients:
            client.send(f"{message}".encode(self.encoding))

    # handle incomming messages and call broadcast()
    def handle(self, client):
        while True:
            try:
                date = datetime.datetime.now().strftime("[%H:%M:%S]")
                message = client.recv(1024).decode(self.encoding)
                self.broadcast(f"{date} {message}")
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.broadcast(f"{nickname} left the chat".encode(self.encoding))
                self.nicknames.remove(nickname)
                break
    
    # handle incomming connections and starting handle for each incomming client
    def client_connection(self):
        while True:
            client, address = self.server.accept()
            self.server_message(f"Connected {str(address)}", True)
            client.send("NICK".encode(self.encoding))
            nickname = client.recv(1024).decode(self.encoding)
            
            if self.find_nick_name(nickname):
                client.send("Err-1".encode(self.encoding))
            else: 
                self.nicknames.append(nickname)
                self.clients.append(client)
                self.all_clients[nickname]=address # add client to all_clients dictionary
                self.broadcast(f"{nickname} joined the chat.")
                client.send("Connected to the server".encode(self.encoding))
                thread = threading.Thread(target=self.handle, args=(client,))
                thread.daemon = True
                thread.start()

server = OmegachatServer()