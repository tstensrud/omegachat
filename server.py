import pickle
import socket
import sys
import threading
import datetime
import time
import tkinter as tk
from server_client import ServerClient
from tkinter import scrolledtext
from tkinter import messagebox
from typing import List


class OmegachatServer:
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 55555
        self.buffer_size = 2048
        self.server = None
        self.clients = [] # list of client objects
        self.server_running = False

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
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        self.root.mainloop()
        

    def frame_resizing(self, event) -> None:
        self.main_frame.config(width=event.width)
    
    def date(self) -> str:
        return datetime.datetime.now().strftime("[%H:%M:%S]")

    # messages the server writes to its own output
    def server_message(self, message: str, date: bool) -> None:
        if date == True:
            self.output.insert(tk.END, f"{self.date()}: {message}\n")
        else:
            self.output.insert(tk.END, f"{message}\n")
        self.output.yview(tk.END)

    # start server and thread for accepting new clients
    def start_server(self) -> None:
        self.server_running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.HOST, self.PORT))
        self.server.listen()
        
        client_thread = threading.Thread(target=self.client_connection)
        client_thread.start()
        self.server_message("Server started.", True)
    
    # stop server
    def stop_server(self) -> None:
        self.server_running = False
        self.server_message(f"Stopped server", True)

    # exit server-program
    def exit(self) -> None:
        if tk.messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.stop_server()
            self.root.destroy()
            sys.exit()

    # find nickname. return True if found
    def find_nick_name(self, name: str) -> bool:
        for i in range(len(self.clients)):
            if self.clients[i].get_nickname() == name:
                return True
        return False

    # list all connected users in the server-output
    def list_connected_users(self):
        if len(self.clients) == 0:
            self.server_message("No users connected", False)
        else:
            self.server_message("Connected users nicknames and IPs:", False)
            for client in self.clients:
                self.server_message(f"Address: {client.get_address()}, username: {client.get_nickname()}", False)

    # find all nicknames from clients-list and return them as a sorted list
    def get_nicknames_list(self) -> List[str]:
        nicknames = []
        for client in self.clients:
            nicknames.append(client.get_nickname())
        nicknames.sort()
        return nicknames


    # broadcast message to all connected users
    def broadcast(self, message) -> None:
        message_out = pickle.dumps(message)
        for client in self.clients:
            try:
                client.get_socket().send(message_out)
            except Exception as e:
                self.server_message(f"Error: {e}", True)


    def return_client_index(self, name: str) -> int:
        for i in range(len(self.clients)):
            if self.clients[i].get_nickname == name:
                return i
        return -1

    # handle incoming messages from a client and call necessary methods based on input
    def handle(self, client) -> None:
        client_socket = client.get_socket()
        nick_name = client.get_nickname()
        while self.server_running == True:
            try:
                message = pickle.loads(client_socket.recv(self.buffer_size))
                if message[0:3] == "msg":
                    self.broadcast(f"msg{self.date()} {message[3:]}")
                elif message[0:3] == "nck":
                    self.broadcast(f"nck{self.get_nicknames_list()}")

            except:
                self.broadcast(f"msg<{nick_name}> left the chat")
                self.broadcast(f"rmv{nick_name}")
                client_socket.close()
                self.clients.pop(self.return_client_index(nick_name))
                break
    
    # handle incoming connections and starting handle() for each incoming client
    def client_connection(self) -> None:
        while self.server_running == True:
            client_socket, ip = self.server.accept()
            nickname = pickle.loads(client_socket.recv(self.buffer_size))
            self.server_message(f"{nickname} connected {str(ip)}", True)
            if self.find_nick_name(nickname):
                error_msg = pickle.dumps("Err-1")
                client_socket.send(error_msg)
            else:
                client = ServerClient(client_socket, ip, nickname)
                self.clients.append(client)
                self.broadcast(f"msg<{client.get_nickname()}> joined the chat.")
                time.sleep(1)
                client_socket.send(pickle.dumps("Connected to the server"))
                thread = threading.Thread(target=self.handle, args=(client,))
                thread.daemon = True
                thread.start()
