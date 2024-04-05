import tkinter as tk
import sys
#import client
from tkinter import scrolledtext

class Omegachat(tk.Tk):

    def frame_resizing(self, event):
        self.chat_frame.config(width=event.width)

    def send(self, event):
        date = 1
        message = self.chat_message.get()
        self.chat_window.insert(tk.END, f"[{date}]: {message}\n")
        self.chat_window.yview(tk.END)
        self.chat_message.delete(0, tk.END)

    def connect():
        pass

    def disconnect():
        pass

    def exit():
        sys.exit()
    
    def login(self):
        
        print(f"1: {self.nickname}")
        self.nickname = self.nick_entry.get()
        print(f"2{self.nickname}")
        self.start_frame.forget()
        self.chat_frame.pack(fill="both", side="left", expand=True)
        self.client_frame.pack(fill="both", side="right")
        self.chat_message.pack(fill="x", side="bottom")
        self.chat_window.pack(side="top", fill="both", expand=True)
        self.alias_list.pack(fill="both", expand=True)

        self.chat_window.insert(tk.END, f"Logged in as {self.nickname}\n")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.nickname = ""
        self.bg_color = "#41464A"
        self.text_color = "white"
        self.window_size = "1024x768"
        self.client_frame_bg ="#7A8373"

        self.title("Omegachat")
        self.config(background=self.bg_color)
        self.geometry(self.window_size)
        
        self.start_frame = tk.Frame(self, bg=self.bg_color)
        self.start_frame.pack(fill="both", expand=True)
        self.nick_label = tk.Label(self.start_frame, text="Nickname", bg=self.bg_color, fg=self.text_color)
        self.nick_label.pack(anchor="center")
        self.nick_entry = tk.Entry(self.start_frame, width=50)
        self.nick_entry.pack(anchor="center", pady=2)
        self.login_button = tk.Button(self.start_frame, text="Login", width=10, height=1, command=self.login)
        self.login_button.pack(anchor="center", pady=10)


        self.chat_frame = tk.Frame(self)
        #self.chat_frame.pack(fill="both", side="left", expand=True)
        self.chat_frame.bind=("<Configure>", self.frame_resizing)

        self.client_frame = tk.Frame(self, bg=self.bg_color, width=200)
        #self.client_frame.pack(fill="both", side="right")

        self.chat_message = tk.Entry(self.chat_frame, bg=self.client_frame_bg, fg="white")
        self.chat_message.bind('<Return>', self.send)
        #self.chat_message.pack(fill="x", side="bottom")

        self.chat_window = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, bg=self.bg_color, fg=self.text_color)
        #self.chat.pack(side="top", fill="both", expand=True)

        self.alias_list = tk.Listbox(self.client_frame, width=25, bg=self.client_frame_bg)
        #self.alias_list.pack(fill="both", expand=True)

        self.menu_bar = tk.Menu(self)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Connect")
        self.options_menu.add_command(label="Disonnect")
        self.options_menu.add_command(label="Exit", command=exit)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.config(menu=self.menu_bar)

if __name__ == "__main__":
    window = Omegachat()
    window.mainloop()
