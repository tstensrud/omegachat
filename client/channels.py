import tkinter as tk
import gui_settings as gs
from tkinter import scrolledtext

class Channel:
    def __init__(self, name: str):
        self.name = name
        self.bg_color = gs.bg_color
        self.text_color = gs.text_color
        self.window_size = gs.window_size
        self.client_frame_bg = gs.client_frame_bg

        self.frame = tk.Frame()
        self.frame.bind = ("<Configure>", self.frame_resizing)
        self.client_frame = tk.Frame(bg=self.bg_color, width=200)

        self.chat_message = tk.Entry(self.frame, bg=self.client_frame_bg, fg="white")
        self.chat_message.bind('<Return>', self.read_chat_message_entry)

        self.chat_window = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, bg=self.bg_color, fg=self.text_color)
        self.chat_window.config(state="disabled")
        self.alias_list = tk.Listbox(self.client_frame, width=25, bg=self.client_frame_bg)
        self.alias_list.config(activestyle="none")

        # self.chat_frame.pack(fill="both", side="left", expand=True)
        self.client_frame.pack(fill="both", side="right")
        self.chat_message.pack(fill="x", side="bottom")
        self.chat_window.pack(side="top", fill="both", expand=True)
        self.alias_list.pack(fill="both", expand=True)

    def frame_resizing(self, event) -> None:
        self.frame.config(width=event.width)

    def read_chat_message_entry(self, event) -> str:
        return self.chat_message.get()

    def get_name(self):
        return self.name
