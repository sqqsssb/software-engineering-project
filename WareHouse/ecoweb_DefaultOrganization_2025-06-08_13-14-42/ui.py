'''
Contains the user interface components for the e-commerce application.
'''
import tkinter as tk
from tkinter import messagebox
class UI:
    def __init__(self, app):
        self.app = app
        self.window = tk.Tk()
        self.window.title("E-commerce Financial Website")
    def create_main_window(self):
        self.window.geometry("800x600")
    def show_home_page(self):
        # Clear the window
        for widget in self.window.winfo_children():
            widget.destroy()
        label = tk.Label(self.window, text="Welcome to the E-commerce Financial Website", font=("Arial", 24))
        label.pack(pady=20)
        login_button = tk.Button(self.window, text="Login", command=self.app.user_auth.login)
        login_button.pack(pady=10)
        register_button = tk.Button(self.window, text="Register", command=self.app.user_auth.register)
        register_button.pack(pady=10)
        self.window.mainloop()