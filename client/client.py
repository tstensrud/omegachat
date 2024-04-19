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
from channels import Channel
from messages import Packet

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

        # entry-field for chat
        self.chat_message = ctk.CTkEntry(self.root)
        self.chat_message.bind('<Return>', self.read_chat_message_entry)

        # status frame
        self.status_channel = Channel(0, "status")
        self.channels.append(self.status_channel)

        # menu
        self.menu_bar = tk.Menu(self.root)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Connect", command=lambda: self.view_frame("login"))
        self.options_menu.add_command(label="Disconnect", command=self.disconnect)
        self.options_menu.add_separator()
        self.options_menu.add_command(label="Exit", command=self.exit)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.channel_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.channel_menu.add_command(label="Status", command=lambda: self.view_frame(self.status_channel))
        self.menu_bar.add_cascade(label="Channels", menu=self.channel_menu)

        self.current_channel = self.login_frame
        self.root.config(menu=self.menu_bar)
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        self.root.mainloop()

    # methods for GUI handling
    def change_window_title(self, channel: str) -> None:
        self.root.title(f"Omegachat - logged in as {self.nickname} -> in {channel}")

    def frame_resizing(self, event) -> None:
        self.login_frame.configure(width=event.width)

    def view_frame(self, channel_frame) -> None:
        if channel_frame == "login": # option from top menu
            if self.current_channel == self.login_frame:
                self.current_channel.forget()
            else:
                self.current_channel.hide_frame()
                self.current_channel = self.login_frame
                self.login_frame.pack(fill="both", expand=True)
                self.nick_entry.pack(pady=10, padx=2)
                self.host_entry.pack(pady=10, padx=2)
                self.port_entry.pack(pady=10, padx=2)
                self.login_button.pack(anchor="center", pady=10)
                self.chat_message.forget()
        else:
            if self.current_channel == self.login_frame:
                self.current_channel.forget()
            else:
                self.current_channel.hide_frame()
            self.current_channel = channel_frame
            self.current_channel.frame.pack(fill="both", expand=True)
            self.chat_message.pack(fill="x", side="bottom")
            self.change_window_title(self.current_channel.get_name())

    # local messages to chat window from the app. always sent to status-frame
    def internal_message(self, message: str) -> None:
        self.status_channel.insert_chat_msg(message)

    def update_alias_list(self, packet) -> None:
        channel = self.get_channel(packet.channel)
        channel.update_alias_listbox(packet.content)

    def channels_menu(self, new_channel: Channel, add: bool) -> None:
        channel_name = new_channel.get_name()
        if add == True:
            self.channel_menu.add_command(label=channel_name, command=lambda: self.view_frame(new_channel))
        else:
            self.channel_menu.delete(self.channel_menu.index(channel_name))

    # chat command-shortcuts
    def chat_commands(self, command: str) -> None:
        if command == "/disconnect":
            self.disconnect()
        elif command[0:5] == "/nick":
            nickname = command[6:]
            self.internal_message(f"New nick is {nickname}")
        elif command[0:5] == "/join":
            channel_name = command[6:]
            self.internal_message(f"Joining {channel_name}")
            self.join_channel(channel_name)
        elif command[0:6] == "/leave":
            self.leave_channel(self.current_channel.get_name())
            self.internal_message(f"Left {self.current_channel}")
        else:
            self.current_channel.insert_chat_msg("Command not found.")

    def get_channel_index(self, channel_name: str) -> int:
        for i in range(len(self.channels)):
            if self.channels[i].get_name() == channel_name:
                return i
        return -1

    def join_channel(self, channel_name: str) -> None:
        for channel in self.channels:
            if channel.get_name() == channel_name:
                self.internal_message(f"Already in {channel_name}")
                break
        new_channel = Channel(len(self.channels) + 1, channel_name)
        self.channels.append(new_channel)
        self.channels_menu(new_channel, True)
        self.broadcast_msg_to_server("join", channel_name, None)
        time.sleep(1)
        self.view_frame(new_channel)

    def leave_channel(self, channel_name: str) -> None:
        channel = self.channels.pop(self.get_channel_index(channel_name))
        self.channels_menu(channel, False)
        channel.frame.destroy()
        time.sleep(1)
        self.view_frame(self.channels[0])
        self.broadcast_msg_to_server("leave", " has lef the channel.", channel_name)


    def get_channel(self, channel_name: str) -> Channel:
        channel = None
        for channel_object in self.channels:
            if channel_object.get_name() == channel_name:
                channel = channel_object
                break
        return channel

    # handle input from user

    def read_chat_message_entry(self, event):
        message = self.chat_message.get()
        self.chat_message.delete(0, tk.END)
        self.client_input_handling(message)
        
    def client_input_handling(self, message: str) -> None:
        if message[0] == "/":
            self.chat_commands(message)
        else:
            if self.current_channel.get_name() == "status":
                self.internal_message(message)
            else:
                self.broadcast_msg_to_server("msg", message, self.current_channel.get_name())

    # disconnect from server
    def disconnect(self) -> None:
        if self.stop_flag == True:
            self.new_messages_from_server_thread(False)
            self.socket.close()
            time.sleep(1)
        self.change_window_title("Not connected")
        self.view_frame("login")
        self.login_widgets_control(False)

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
                if packet.id == "msg": # if true packet_content is a string
                    if packet.channel != None:
                        channel = self.get_channel(packet.channel)
                        channel.insert_chat_msg(f"[{packet.date}] <{packet.owner}> {packet.content}")
                    else:
                        self.internal_message(packet.content)
                elif packet.id == "updusr":
                    self.update_alias_list(packet)
                elif packet.id == "join": # if true packet_content is a string
                    try:
                        channel = self.get_channel(packet.channel)
                        self.internal_message(f"Joined {packet.channel}")
                        channel.insert_chat_msg(packet.content)
                    except Exception as e:
                        print(f"Error on joining: {e}")
                elif packet.id == "server":
                    self.internal_message(packet.content)
            except EOFError as eof:
                print(f"EOFerror: {eof}")
                self.socket.close()
                break
            except Exception as e:
                print(f"Client disconnected: {e}\n")
                self.socket.close()
                break

    # disable login-widgest when connected to avoid trying to connect while connection is up
    def login_widgets_control(self, connected: bool):
        if connected == True:
            self.nick_entry.configure(state="disabled")
            self.host_entry.configure(state="disabled")
            self.port_entry.configure(state="disabled")
            self.login_button.configure(state="disabled")
        else:
            self.nick_entry.configure(state="normal")
            self.host_entry.configure(state="normal")
            self.port_entry.configure(state="normal")
            self.login_button.configure(state="normal")

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
            self.internal_message("--// STATUS //--")
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
                self.view_frame(self.channels[0])
                self.internal_message(f"Connected to {HOST}.")
                self.internal_message(f"Welcome to our server. Join a channel by typing /join channel_name")
                self.login_widgets_control(True)

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
    def broadcast_msg_to_server(self, packet_id: str, content, channel: str) -> None:
        date = datetime.datetime.now().strftime("%H:%M:%S")
        new_packet = Packet(packet_id, date, self.nickname, content, channel)
        try:
            self.socket.send(pickle.dumps(new_packet))
        except Exception as e:
            print(f"broadcast error: {e}")