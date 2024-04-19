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
from messages import Packet
from channels import Channel

class OmegachatServer:
    def __init__(self):
        self.HOST = "127.0.0.1"
        self.PORT = 55555
        self.buffer_size = 2048
        self.server = None
        self.clients = [] # list of connected client objects
        self.channels = [] # list of channel objects
        self.server_running = False
        self.channel_general = Channel("General", "Welcome to the main-channel!")
        self.channels.append(self.channel_general)

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
        self.users_menu.add_command(label="List channels", command=self.list_all_channels)
        self.menu_bar.add_cascade(label="Stats", menu=self.users_menu)
        
        self.root.config(menu=self.menu_bar)
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        self.root.mainloop()
        

    def frame_resizing(self, event) -> None:
        self.main_frame.config(width=event.width)
    
    def date(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    # messages the server writes to its own output
    def server_message(self, message: str, date: bool) -> None:
        self.output.config(state="normal")
        if date == True:
            self.output.insert(tk.END, f"{self.date()}: {message}\n")
        else:
            self.output.insert(tk.END, f"{message}\n")
        self.output.config(state="disabled")
        with open("log.txt", "a") as file:
            file.write(f"{self.date()}: {message}\n")
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
        if self.server_running:
            if len(self.clients) == 0:
                self.server_message("No users connected", False)
            else:
                self.server_message("Connected users nicknames and IPs:", False)
                for client in self.clients:
                    self.server_message(f"Address: {client.get_address()}, username: {client.get_nickname()}", False)
        else:
            self.server_message("Server is not running", False)
    # list all channels
    def list_all_channels(self):
        if self.server_running:
            for channel in self.channels:
                self.server_message(f"Channel: {channel.get_name()} - {channel.get_user_list().get_users()}", False)
        else:
            self.server_message("Server is not running.", False)

    # find all nicknames from clients-list and return them as a sorted list
    def get_nicknames_list(self) -> List[str]:
        nicknames = []
        for client in self.clients:
            nicknames.append(client.get_nickname())
        nicknames.sort()
        return nicknames

    # if channel exists, add user to its user list. If not create new channel
    def join_channel(self, channel: str, nick_name: str) -> None:
        client = None
        channel_user_list = []
        response = None
        for client_object in self.clients:
            if client_object.get_nickname() == nick_name:
                client = client_object
                break
        if self.get_channel_object(channel) == None:
            new_channel = Channel(channel, "MOTD")
            new_channel.user_list.add_user(nick_name)
            self.channels.append(new_channel)
            response = pickle.dumps(Packet("join", self.date(), None, f"Joined {channel}", channel))
            channel_user_list = new_channel.get_user_list().get_users()

        else:
            existing_channel = self.get_channel_object(channel)
            channel_user_list = existing_channel.get_user_list().get_users()
            existing_channel.user_list.add_user(nick_name)
            response = pickle.dumps(Packet("join", self.date(), None, existing_channel.get_motd(), channel))
        try:
            client.get_socket().send(response)
        except Exception as e:
            self.server_message(f"Error on joining channel: {e}", True)
        self.get_user_object(nick_name).add_channel(channel)
        updated_list = Packet("updusr", self.date(), nick_name, channel_user_list, channel)
        self.broadcast(updated_list)

    def remove_channel_if_channel_is_empty(self, channel: Channel) -> None:
        index = self.get_channel_index(channel.get_name())
        self.channels.pop(index)

    def leave_channel(self, packet) -> None:
        channel_object = self.get_channel_object(packet.channel)
        channel_object.get_user_list().remove_user(packet.owner)
        self.get_user_object(packet.owner).remove_channel(packet.channel)
        if len(channel_object.get_user_list().get_users()) == 0:
            self.remove_channel_if_channel_is_empty(channel_object)
        else:
            update_to_users = Packet("updusr", self.date(), packet.owner, channel_object.get_user_list().get_users(), packet.channel)
            self.broadcast(update_to_users)

    # removes user from all channels in case of diconnect or exit
    def client_quit(self, client):
        client_channel_list = client.get_channels()
        for channel in client_channel_list:
            channel_object = self.get_channel_object(channel)
            self.get_channel_object(channel).get_user_list().remove_user(client.get_nickname())
            update_to_users = Packet("updusr", self.date(), client.get_nickname(), channel_object.get_user_list().get_users(), channel_object.get_name())
            self.broadcast(update_to_users)

            # if client is only user in channel, remove channel from server after user quits
            if len(channel_object.get_user_list().get_users()) == 0:
                self.remove_channel_if_channel_is_empty(channel_object)
    def get_user_object(self, nickname):
        for user_object in self.clients:
            if user_object.get_nickname() == nickname:
                return user_object

    # searches for existing channel. returns None if not found
    def get_channel_object(self, channel: str):
        for channel_object in self.channels:
            if channel_object.get_name() == channel:
                return channel_object
        return None

    def send_to_single_client(self, msg_id, message, client) -> None:
        message_out = Packet(msg_id, self.date(), None, message, None)
        try:
            client.get_socket.send(pickle.dumps(message_out))
        except Exception as e:
            self.server_message(f"Error sending to single client: {e}", True)

    # return the user-list of a channel
    def get_channel_users(self, channel_name: str) -> List[str]:
        user_list = None
        for channel in self.channels:
            if channel.get_name() == channel_name:
                user_list = channel.get_user_list().get_users()
                return user_list

    def get_channel_index(self, channel_name: str) -> int:
        for i in range(len(self.channels)):
            if self.channels[i].get_name() == channel_name:
                return i
        return -1

    # broadcast message to correct channel
    # message is an object of Message
    def broadcast(self, packet) -> None:
        message_out = pickle.dumps(packet)
        channel_name = packet.channel
        if channel_name != None:
            channel_users = self.get_channel_users(channel_name)
            for client in channel_users:
                try:
                    self.get_user_object(client).get_socket().send(message_out)
                except Exception as e:
                    self.server_message(f"Error broadcasting to specific channels: {e}", True)
        else:
            for client in self.clients:
                try:
                    client.get_socket().send(message_out)
                except Exception as e:
                    self.server_message(f"Error broadcasting to all channels: {e}", True)

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
                packet = pickle.loads(client_socket.recv(self.buffer_size))
                if packet.id == "msg":
                    self.broadcast(packet)
                elif packet.id == "join":
                    self.join_channel(packet.content, nick_name)
                elif packet.id == "leave":
                    self.leave_channel(packet)
            except:
                self.client_quit(client)
                client_socket.close()
                self.clients.pop(self.return_client_index(nick_name))
                break
    
    # handle incoming connections and starting handle() for each incoming client
    def client_connection(self) -> None:
        while self.server_running == True:
            client_socket, ip = self.server.accept()
            nickname = pickle.loads(client_socket.recv(self.buffer_size))
            if self.find_nick_name(nickname):
                error_msg = pickle.dumps("Err-1")
                client_socket.send(error_msg)
            else:
                self.server_message(f"{nickname} connected {str(ip)}", True)
                client = ServerClient(client_socket, ip, nickname)
                self.clients.append(client)
                nickname = client.get_nickname()
                welcome_msg = Packet("server", self.date(), nickname, f"Successfully connected", None)
                client_socket.send(pickle.dumps(welcome_msg))
                time.sleep(1)
                thread = threading.Thread(target=self.handle, args=(client,))
                thread.daemon = True
                thread.start()
