import tkinter as tk
import customtkinter as ctk
from CTkListbox import *

class Channel:
    def __init__(self, id: int, name: str):
        self.name = name
        self.id = id
        self.frame = tk.Frame()
        self.frame.bind = ("<Configure>", self.frame_resizing)
        self.client_frame = ctk.CTkFrame(self.frame)

        self.chat_message = ctk.CTkEntry(self.frame)
        self.chat_message.bind('<Return>', self.read_chat_message_entry)

        self.chat_window = ctk.CTkTextbox(self.frame, wrap=tk.WORD)
        self.chat_window.configure(state="disabled")
        self.alias_list = CTkListbox(self.client_frame, width=200)

        # self.chat_frame.pack(fill="both", side="left", expand=True)
        self.client_frame.pack(fill="both", side="right")
        self.chat_message.pack(fill="x", side="bottom")
        self.chat_window.pack(side="top", fill="both", expand=True)
        self.alias_list.pack(fill="both", expand=True)

    def frame_resizing(self, event) -> None:
        self.frame.config(width=event.width)
    def get_name(self):
        return self.name
    def hide_frame(self):
        self.frame.forget()
    def get_id(self) -> int:
        return self.id

    def read_chat_message_entry(self, event) -> str:
        message = self.chat_message.get()
        self.chat_message.delete(0, tk.END)
        self.client_input_handling(message)

    def insert_chat_msg(self, message: str) -> None:
        self.chat_window.configure(state="normal")
        self.chat_window.insert(tk.END, f"{message}\n")
        self.chat_window.configure(state="disabled")
        self.chat_window.yview(tk.END)

    def client_input_handling(self, message: str) -> None:
        if message[0] == "/":
            pass
        else:
            #self.broadcast_msg_to_server("msg", message, self.current_channel.get_name())
            self.insert_chat_msg(message)