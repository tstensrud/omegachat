import socket
import time
import tkinter as tk
import sys
import threading
from tkinter import messagebox
from tkinter import scrolledtext

class Client:
    def __init__(self):
        self.nickname: str = ""
        self.encoding = "utf-8"
        self.socket = None
        self.connected_users = [] 

        # flag for the receive msg thread
        self.stop_flag = False

        # GUI colors and configs
        self.bg_color = "#41464A"
        self.text_color = "white"
        self.window_size = "1024x768"
        self.client_frame_bg ="#7A8373"
        
        self.root = tk.Tk()
        self.root.title("Omegachat")
        self.root.config(background=self.bg_color)
        self.root.geometry(self.window_size)

        self.start_frame = tk.Frame(self.root, bg=self.bg_color)
        self.start_frame.pack(fill="both", expand=True)
        self.nick_entry = tk.Entry(self.start_frame, width=50)
        self.nick_entry.pack(pady=10, padx=2)
        self.nick_entry.insert(0, "Username")
        self.host_entry = tk.Entry(self.start_frame, width=50)
        self.host_entry.pack(pady=10, padx=2)
        self.host_entry.insert(0, "127.0.0.1")
        self.port_entry = tk.Entry(self.start_frame, width=50)
        self.port_entry.pack(pady=10, padx=2)
        self.port_entry.insert(0, "55555")
        self.login_button = tk.Button(self.start_frame, text="Login", width=10, height=1, command=self.login_gui)
        self.login_button.pack(anchor="center", pady=10)

        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.bind=("<Configure>", self.frame_resizing)

        self.client_frame = tk.Frame(bg=self.bg_color, width=200)

        self.chat_message = tk.Entry(self.chat_frame, bg=self.client_frame_bg, fg="white")
        self.chat_message.bind('<Return>', self.read_chat_message_entry)

        self.chat_window = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, bg=self.bg_color, fg=self.text_color)  

        self.alias_list = tk.Listbox(self.client_frame, width=25, bg=self.client_frame_bg)

        self.menu_bar = tk.Menu(self.root)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Connect")
        self.options_menu.add_command(label="Disonnect", command=self.disconnect)
        self.options_menu.add_command(label="Exit", command=self.exit)
        self.options_menu.add_command(label="Test", command=self.update_alias_list)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        self.root.config(menu=self.menu_bar)
        self.root.mainloop()

    # methods for GUI handling
    def change_window_title(self, title) -> None:
        self.root.title(f"Omegachat - logged in as {title}")
    def frame_resizing(self, event) -> None:
        self.chat_frame.config(width=event.width)
    def internal_message(self, message) -> None: # local messages to chat window from the app
        self.chat_window.insert(tk.END, f"{message}\n")
        self.chat_window.yview(tk.END)
    def update_alias_list(self) -> None:
        #nicknames = self.input_handling("nicknames", True) # que for server to send nickname-list
        self.client_input_handling("Alias list", False)
        
    def read_chat_message_entry(self, event): # read chat entry-field
        entry_field = self.chat_message.get()
        self.client_input_handling(entry_field, True)
    
    # chat command-shortcuts
    def chat_commands(self, command) -> None:
        if command == "disconnect":
            self.disconnect()
        elif command == "nick":
            self.internal_message("nick")
        else:
            self.internal_message("Command not found.")

    # read input from chat_entry and handle it.
    # set broadcast True if message is for other chatters.
    # set broadcast False if its to call server or local client methods
    def client_input_handling(self, message, broadcast) -> None:
        if broadcast == True: # if regulare chat message
            # if input from chat-entry is a /-command
            if message[0] == "/":
                self.chat_commands(message[1:])
                self.chat_message.delete(0, tk.END)
                self.chat_window.yview(tk.END)
            else:
                # ">" is added to seperate regular chat messages from server-calls on server side.
                self.broadcast_msg_to_server(f">{self.nickname}: {message}")
                self.chat_message.delete(0, tk.END)
                self.chat_window.yview(tk.END)
        if broadcast == False:
            self.broadcast_msg_to_server(message) # used for a request to server

            
    
    
            
    # disconnect from server
    def disconnect(self) -> None:
        self.new_messages_from_server_thread(False)
        self.socket.close()
        time.sleep(1)
        self.chat_window.insert(tk.END, "Disconnected.")

    def exit(self) -> None:
        try:
            self.disconnect()
            sys.exit()
        except Exception as e:
            print(e)
            self.disconnect()
            sys.exit(1)

    # receive new messages from server and write them to chat window
    def incomming_messages_from_server(self) -> None:
        while self.stop_flag == True:
            try:
                message=self.socket.recv(1024).decode(self.encoding)
                self.chat_window.insert(tk.END, f"{message}\n")
                self.chat_window.yview(tk.END)
            except Exception as e:
                print(f"Disconnected: {e} \n")
                self.socket.close()
                break 

    # logging in and establishing connection to the server through a web socket.
    # if chosen nickname is already taken it closes the socket and returns
    def login_gui(self) -> None:
        nick = self.nick_entry.get()
        HOST = self.host_entry.get()

        try: # controll that port-number is numbers only
            PORT = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Port can only be digits")
            return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, PORT))
            self.internal_message(f"Connecting to: {HOST}:{PORT}")
            self.socket.send(f"{nick}".encode(self.encoding), True) # send nick to server
            nick_response = self.socket.recv(1024).decode(self.encoding) # receives response on nick. will be "err-1" if nick is taken
            
            if nick_response == "Err-1":
                messagebox.showerror("Error", "Name is already taken")
                self.socket.close()
                return
            else:
                self.nickname = nick
                # forget login-frame and pack the chat-frames
                self.start_frame.forget()
                self.chat_frame.pack(fill="both", side="left", expand=True)
                self.client_frame.pack(fill="both", side="right")
                self.chat_message.pack(fill="x", side="bottom")
                self.chat_window.pack(side="top", fill="both", expand=True)
                self.alias_list.pack(fill="both", expand=True)

                self.internal_message(nick_response)
                self.change_window_title(self.nickname)
                self.new_messages_from_server_thread(True)

                print("Nick accepted")
        except Exception as e:
            print(f"Connection-error: {e}")
    
    # multi thread for receiving new messages from server
    def new_messages_from_server_thread(self, running) -> None:
        if running == True:
            self.stop_flag = True
            receive_message_from_server = threading.Thread(target=self.incomming_messages_from_server)
            receive_message_from_server.start()
        if running == False:
            self.stop_flag = False
    
    # broadcast encoded message to server
    def broadcast_msg_to_server(self, message) -> None:
        self.socket.send(message.encode(self.encoding))