import tkinter as tk
import customtkinter as ctk
from CTkListbox import *

class Channel:
    def __init__(self, id: int, name: str):
        self.name = name
        self.id = id
        #self.active_users = []
        self.frame = tk.Frame()
        self.frame.bind = ("<Configure>", self.frame_resizing)
        self.client_frame = ctk.CTkFrame(self.frame)
        self.chat_window = ctk.CTkTextbox(self.frame, wrap=tk.WORD)
        self.chat_window.configure(state="disabled")
        self.alias_list = CTkListbox(self.client_frame, width=200)
        self.client_frame.pack(fill="both", side="right")
        self.chat_window.pack(side="top", fill="both", expand=True)
        self.alias_list.pack(fill="both", expand=True)

    def frame_resizing(self, event) -> None:
        self.frame.config(width=event.width)

    def get_name(self) -> str:
        return self.name

    def hide_frame(self) -> None:
        self.frame.forget()

    def get_id(self) -> int:
        return self.id

    def update_alias_listbox(self, user_list) -> None:
        self.alias_list.delete(0, tk.END)
        for user in user_list:
            self.alias_list.insert(tk.END, user)

    def insert_chat_msg(self, message: str) -> None:
        self.chat_window.configure(state="normal")
        self.chat_window.insert(tk.END, f"{message}\n")
        self.chat_window.configure(state="disabled")
        self.chat_window.yview(tk.END)
