'''
Contains the GUI components for the online shopping system.
'''
import tkinter as tk
class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Online Shopping System")
        self.root.geometry("800x600")  # Set window size
    def run(self):
        self.root.mainloop()
    # Additional GUI methods can be added here