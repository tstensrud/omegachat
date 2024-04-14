import ast
import pickle
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
        self.buffer_size = 2048
        self.socket = None

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
        self.alias_list.config(activestyle="none")

        self.menu_bar = tk.Menu(self.root)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Connect")
        self.options_menu.add_command(label="Disonnect", command=self.disconnect)
        self.options_menu.add_command(label="Exit", command=self.exit)
        self.options_menu.add_command(label="Test")
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        self.root.config(menu=self.menu_bar)
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        self.root.mainloop()

    # methods for GUI handling
    def change_window_title(self, title: str) -> None:
        self.root.title(f"Omegachat - logged in as {title}")
    def frame_resizing(self, event) -> None:
        self.chat_frame.config(width=event.width)
    def internal_message(self, message: str) -> None: # local messages to chat window from the app
        self.chat_window.insert(tk.END, f"{message}\n")
        self.chat_window.yview(tk.END)
    def update_alias_list(self, input_string, add: bool) -> None:
        if add == True:
            self.alias_list.delete(0, tk.END)
            evaluate = ast.literal_eval(input_string)
            updated_nicknames = []
            for nickname in evaluate:
                updated_nicknames.append(nickname)
            updated_nicknames.sort()
            for nickname in updated_nicknames:
                self.alias_list.insert(tk.END, nickname)
        elif add == False:
            list_of_names = self.alias_list.get(0, tk.END)
            for i in range(len(list_of_names)):
                if list_of_names[i] == input_string:
                    self.alias_list.delete(i)
                    break
        
    def read_chat_message_entry(self, event): # read chat entry-field
        entry_field = self.chat_message.get()
        self.client_input_handling(entry_field, False)
    
    # chat command-shortcuts
    def chat_commands(self, command: str) -> None:
        if command == "disconnect":
            self.disconnect()
        elif command == "nick":
            self.internal_message("nick")
        else:
            self.internal_message("Command not found.")

    # read input from chat_entry and handle it.
    # set broadcast True if message is for other chatters.
    # set broadcast False if its to call server or local client methods
    def client_input_handling(self, message: str, server_request: bool) -> None:
        if server_request == False:
            if message[0] == "/":
                self.chat_commands(message[1:])
                self.chat_message.delete(0, tk.END)
                self.chat_window.yview(tk.END)
            else:
                self.broadcast_msg_to_server(f"msg<{self.nickname}> {message}")
                self.chat_message.delete(0, tk.END)
                self.chat_window.yview(tk.END)
        else:
            self.broadcast_msg_to_server(message) # used to call methods on server
            
    # disconnect from server
    def disconnect(self) -> None:
        if self.stop_flag == True:
            self.new_messages_from_server_thread(False)
            self.socket.close()
            time.sleep(1)
        self.chat_frame.forget()
        self.client_frame.forget()
        self.chat_message.forget()
        self.chat_window.forget()
        self.alias_list.forget()
        self.change_window_title("Not connected")
        self.start_frame.pack(fill="both", expand=True)

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
                message = pickle.loads(self.socket.recv(self.buffer_size))
                if message[0:3] == "rmv":
                    self.update_alias_list(message[3:], False)
                elif message[0:3] == "msg":
                    self.chat_window.insert(tk.END, f"{message[3:]}\n")
                    self.chat_window.yview(tk.END)
                elif message[0:3] == "nck":
                    self.update_alias_list(message[3:], True)
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
                self.start_frame.forget()
                self.chat_frame.pack(fill="both", side="left", expand=True)
                self.client_frame.pack(fill="both", side="right")
                self.chat_message.pack(fill="x", side="bottom")
                self.chat_window.pack(side="top", fill="both", expand=True)
                self.alias_list.pack(fill="both", expand=True)
                self.change_window_title(self.nickname)
                time.sleep(1)
                self.internal_message(nick_response)
                self.broadcast_msg_to_server("nck")

                print("Nick accepted")
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
    def broadcast_msg_to_server(self, message: str) -> None:
        self.socket.send(pickle.dumps(message))