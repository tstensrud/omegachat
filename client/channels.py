import tkinter as tk
import customtkinter as ctk
from CTkListbox import *

class Channel:
    def __init__(self, name: str):
        self.name = name
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

    def read_chat_message_entry(self, event) -> str:
        return self.chat_message.get()
    def insert_chat_msg(self, message: str) -> None:
        self.chat_window.insert(tk.END, f"{message}\n")

    def get_name(self):
        return self.name

    def forget(self):
        self.frame.forget()
