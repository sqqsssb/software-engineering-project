'''
This module contains the MainApp class which sets up the GUI for the application.
'''
import tkinter as tk
class MainApp:
    '''
    Main application class that creates the GUI.
    '''
    def __init__(self):
        '''
        Initializes the main window and its components.
        '''
        self.root = tk.Tk()
        self.root.title("Say Hi App")
        self.label = tk.Label(self.root, text="Click the button to say Hi!")  # Updated line
        self.label.pack(pady=20)
        self.button = tk.Button(self.root, text="Say Hi", command=self.say_hi)
        self.button.pack(pady=10)
        # Bind the window close event to a method
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    def say_hi(self):
        '''
        Updates the label to display "Hi" when the button is clicked.
        '''
        self.label.config(text="Hi")
    def on_closing(self):
        '''
        Handles the window close event.
        '''
        self.root.destroy()  # Closes the application
    def run(self):
        '''
        Starts the main loop of the application.
        '''
        self.root.mainloop()