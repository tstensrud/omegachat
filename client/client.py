import pickle
import socket
import time
import tkinter as tk
import customtkinter as ctk
import sys
import threading
import datetime
from typing import List
from tkinter import messagebox
from messages import Packet
from channels import Channel

class Client:
    def __init__(self):
        self.nickname: str = ""
        self.socket = None
        self.buffer_size: int = 2048

        # flag for the receive msg thread
        self.stop_flag: bool = False
        self.channels: List[Channel] = []

        # GUI config
        self.window_size = "1024x768"

        # root window
        self.root = tk.Tk()
        self.root.title("Omegachat")
        self.root.geometry(self.window_size)
        self.root.config(bg="black")

        # log-in frame
        self.login_frame = ctk.CTkFrame(self.root)
        self.login_frame.pack(fill="both", expand=True)
        self.nick_entry = ctk.CTkEntry(self.login_frame)
        self.nick_entry.pack(pady=10, padx=2)
        self.nick_entry.insert(0, "Username")
        self.host_entry = ctk.CTkEntry(self.login_frame)
        self.host_entry.pack(pady=10, padx=2)
        self.host_entry.insert(0, "127.0.0.1")
        self.port_entry = ctk.CTkEntry(self.login_frame)
        self.port_entry.pack(pady=10, padx=2)
        self.port_entry.insert(0, "55555")
        self.login_button = ctk.CTkButton(self.login_frame, text="Login", command=self.login_gui)
        self.login_button.pack(anchor="center", pady=10)

        # status frame
        self.status_frame = ctk.CTkFrame(self.root)
        self.status_window = ctk.CTkTextbox(self.status_frame, wrap=tk.WORD)
        self.status_window.configure(state="disabled")
        self.status_entry = ctk.CTkEntry(self.status_frame)
        self.status_entry.bind('<Return>', self.read_chat_message_entry)


        self.chat_frame = ctk.CTkFrame(self.root)
        self.chat_frame.bind = ("<Configure>", self.frame_resizing)
        self.client_frame = ctk.CTkFrame(self.root, width=200)
        self.chat_message = ctk.CTkEntry(self.chat_frame)
        self.chat_message.bind('<Return>', self.read_chat_message_entry)
        self.chat_window = ctk.CTkTextbox(self.chat_frame, wrap=tk.WORD)
        self.chat_window.configure(state="disabled")
        self.alias_list = tk.Listbox(self.client_frame, width=25)
        self.alias_list.config(activestyle="none")

        # menu
        self.menu_bar = tk.Menu(self.root)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Connect", command=lambda: self.view_frame("login"))
        self.options_menu.add_command(label="Disconnect", command=self.disconnect)
        self.options_menu.add_separator()
        self.options_menu.add_command(label="Exit", command=self.exit)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.channel_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.channel_menu.add_command(label="Status", command=lambda: self.view_frame("status"))
        self.menu_bar.add_cascade(label="Channels", menu=self.channel_menu)

        self.current_frame = self.login_frame
        self.root.config(menu=self.menu_bar)
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        self.root.mainloop()

    # methods for GUI handling
    def change_window_title(self, title: str) -> None:
        self.root.title(f"Omegachat - logged in as {title}")

    def frame_resizing(self, event) -> None:
        self.chat_frame.configure(width=event.width)

    def view_frame(self, frame) -> None:
        if frame == "status":
            self.current_frame.forget()
            self.current_frame = self.status_frame
            self.status_frame.pack(fill="both", expand=True)
            self.status_entry.pack(fill="x", side="bottom")
            self.status_window.pack(side="top", fill="both", expand=True)
        elif frame == "login":
            self.current_frame.forget()
            self.current_frame = self.login_frame
            self.login_frame.pack(fill="both", expand=True)
            self.nick_entry.pack(pady=10, padx=2)
            self.host_entry.pack(pady=10, padx=2)
            self.port_entry.pack(pady=10, padx=2)
            self.login_button.pack(anchor="center", pady=10)
        else:
            self.current_frame.forget()
            self.current_frame = frame
            self.current_frame.frame.pack(fill="both", expand=True)


    def internal_message(self, message: str) -> None: # local messages to chat window from the app
        self.status_window.configure(state="normal")
        self.status_window.insert(tk.END, f"{message}\n")
        self.status_window.configure(state="disabled")
        self.status_window.yview(tk.END)

    def update_alias_list(self, packet) -> None:
        self.alias_list.delete(0, tk.END)
        new_alias_list = packet
        for new_alias in new_alias_list:
            self.alias_list.insert(tk.END, new_alias)

    def channels_menu(self, new_channel: Channel, add: bool) -> None:
        if add == True:
            channel_name = new_channel.get_name()
            self.channel_menu.add_command(label=channel_name, command=lambda: self.view_frame(new_channel))
        else:
            pass # remove menu-item

    def read_chat_message_entry(self, event): # read chat entry-field
        entry = self.status_entry.get()
        self.status_entry.delete(0, tk.END)
        self.client_input_handling(entry)

    
    # chat command-shortcuts
    def chat_commands(self, command: str) -> None:
        if command == "/disconnect":
            self.disconnect()
        elif command[0:5] == "/nick":
            command = command[6:]
            self.internal_message(f"New nick is {command}")
        elif command[0:5] == "/join":
            command = command[6:]
            self.internal_message(f"Joining {command}")
            self.join_channel(command)
        elif command[0:6] == "/leave":
            command = command[7:]
            self.internal_message(f"Left {command}")
        else:
            self.internal_message("Command not found.")

    def join_channel(self, channel_name: str) -> None:
        for channel in self.channels:
            if channel.get_name() == channel_name:
                self.internal_message(f"Already in {channel_name}")
                break
        new_channel = Channel(channel_name)
        self.channels.append(new_channel)
        self.channels_menu(new_channel, True)
        self.broadcast_msg_to_server("join", channel_name, None)
        time.sleep(1)
        self.view_frame(new_channel)

    def get_channel(self, channel_name: str):
        for channel in self.channels:
            if channel.get_name() == channel_name:
                print(channel.get_name())
                return channel
        return None

    # handle input from user
    def client_input_handling(self, message: str) -> None:
        if message[0] == "/":
            self.chat_commands(message)
            self.chat_message.delete(0, tk.END)
            self.chat_window.yview(tk.END)
        else:
            self.broadcast_msg_to_server(message)
            self.chat_message.delete(0, tk.END)
            self.chat_window.yview(tk.END)

    # disconnect from server
    def disconnect(self) -> None:
        if self.stop_flag == True:
            self.new_messages_from_server_thread(False)
            self.socket.close()
            time.sleep(1)
        self.change_window_title("Not connected")
        self.login_frame.pack(fill="both", expand=True)

    def exit(self) -> None:
        if tk.messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            try:
                self.disconnect()
                self.root.destroy()
                sys.exit()
            except Exception as e:
                print(e)
                self.disconnect()
                self.root.destroy()
                sys.exit(1)

    # receive new messages from server and write them to chat window
    def incoming_messages_from_server(self) -> None:
        while self.stop_flag == True:
            try:
                packet = pickle.loads(self.socket.recv(self.buffer_size))
                packet_id = packet.id
                packet_date = packet.date
                packet_owner = packet.owner
                packet_content = packet.content
                packet_channel = packet.channel
                if packet_id == "msg":
                    channel = self.get_channel(packet_channel)
                    print(f"CHANNEL: {channel}")
                    channel.chat_window.configure(state="normal")
                    channel.chat_window.insert(tk.END, f"[{packet_date}] <{packet_owner}> {packet_content}\n")
                    channel.chat_window.configure(state="disabled")
                    channel.chat_window.yview(tk.END)
                elif packet_id == "uptusr":
                    #self.update_alias_list(packet.content)
                    pass
            except Exception as e:
                print(f"Client disconnected: {e} \n")
                self.socket.close()
                break

    # logging in and establishing connection to the server through a web socket.
    # if chosen nickname is already taken it closes the socket and returns
    def login_gui(self) -> None:
        nick = self.nick_entry.get()
        HOST = self.host_entry.get()

        try: # control that port-number is numbers only
            PORT = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Port can only be digits")
            return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, PORT))
            self.internal_message(f"Connecting to: {HOST}:{PORT}")
            self.socket.send(pickle.dumps(f"{nick}")) # send nick to server
            nick_response = pickle.loads(self.socket.recv(self.buffer_size)) # receives response on nick. will be "err-1" if nick is taken
            
            if nick_response == "Err-1":
                messagebox.showerror("Error", "Name is already taken")
                self.socket.close()
                return
            else:
                self.new_messages_from_server_thread(True)
                self.nickname = nick
                # forget login-frame and pack the chat-frames
                self.view_frame("status")
                self.internal_message(f"Connected to {HOST}.")
                self.internal_message(f"Welcome to our server. Join a channel by typing /join channel_name")
                time.sleep(1)
        except Exception as e:
            print(f"Connection-error: {e}")
    
    # multi thread for receiving new messages from server
    def new_messages_from_server_thread(self, running: bool) -> None:
        if running == True:
            self.stop_flag = True
            receive_message_from_server = threading.Thread(target=self.incoming_messages_from_server)
            receive_message_from_server.start()
        if running == False:
            self.stop_flag = False
    
    # broadcast encoded message to server
    def broadcast_msg_to_server(self, id: str, packet, channel: str) -> None:
        date = datetime.datetime.now().strftime("%H:%M:%S")
        new_packet = Packet(id, date, self.nickname, packet, channel)
        self.socket.send(pickle.dumps(new_packet))