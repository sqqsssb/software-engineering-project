'''
GUI class to handle the graphical user interface of the application.
'''
import tkinter as tk
class GUI:
    def create_main_window(self):
        self.window = tk.Tk()
        self.window.title("Online Shopping System")
        self.create_user_interface()
        self.window.mainloop()
    def create_user_interface(self):
        # Logic to create user interface components
        label = tk.Label(self.window, text="Welcome to the Online Shopping System")
        label.pack()