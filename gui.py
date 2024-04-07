import time
import tkinter as tk
import sys
import threading
from tkinter import messagebox
from tkinter import scrolledtext
from client import Client

class Gui:
    def __init__(self):
        self.client = Client(None, None, None, None)
        self.encoding = "ascii"
        
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
        self.nick_label = tk.Label(self.start_frame, text="Nickname", bg=self.bg_color, fg=self.text_color)
        self.nick_label.pack(anchor="center")
        self.nick_entry = tk.Entry(self.start_frame, width=50)
        self.nick_entry.pack(anchor="center", pady=2)
        self.login_button = tk.Button(self.start_frame, text="Login", width=10, height=1, command=self.login_gui)
        self.login_button.pack(anchor="center", pady=10)

        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.bind=("<Configure>", self.frame_resizing)

        self.client_frame = tk.Frame(bg=self.bg_color, width=200)

        self.chat_message = tk.Entry(self.chat_frame, bg=self.client_frame_bg, fg="white")
        self.chat_message.bind('<Return>', self.send)

        self.chat_window = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, bg=self.bg_color, fg=self.text_color)  

        self.alias_list = tk.Listbox(self.client_frame, width=25, bg=self.client_frame_bg)

        self.menu_bar = tk.Menu(self.root)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Connect")
        self.options_menu.add_command(label="Disonnect", command=self.disconnect)
        self.options_menu.add_command(label="Exit", command=exit)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        self.root.config(menu=self.menu_bar)
        self.root.mainloop()


    def client_object(self):
        return self.client
   
    def frame_resizing(self, event):
        self.chat_frame.config(width=event.width)

    def send(self, event):
        message = self.chat_message.get()
        self.client.write(message)
        self.chat_message.delete(0, tk.END)
        self.chat_window.yview(tk.END)

    def disconnect(self):
        self.newmsg_thread(False)
        self.client.disconnect()
        time.sleep(1)
        self.chat_window.insert(tk.END, "Disconnected.")

    def exit(self):
        self.disconnect()
        sys.exit()

    def new_message(self):
        while self.stop_flag == True:
            try:
                message=self.client.client.recv(1024).decode(self.encoding)
                self.chat_window.insert(tk.END, f"{message}\n")
                self.chat_window.yview(tk.END)
            except Exception as e:
                print(f"Disconnected: {e} \n")
                self.client.client.close()
                break 

    def login_gui(self): 
        connect = self.client.login(self.nick_entry.get())
        if connect == "Err-1":
            messagebox.showerror("Error", "Name is allready taken")
            return
        else:
            self.start_frame.forget()
            self.chat_frame.pack(fill="both", side="left", expand=True)
            self.client_frame.pack(fill="both", side="right")
            self.chat_message.pack(fill="x", side="bottom")
            self.chat_window.pack(side="top", fill="both", expand=True)
            self.alias_list.pack(fill="both", expand=True)
            
            self.newmsg_thread(True)
    
    def newmsg_thread(self, running):
        if running == True:
            self.stop_flag = True
            receive_message_from_server = threading.Thread(target=self.new_message)
            receive_message_from_server.start()
        if running == False:
            self.stop_flag = False
            

    

        