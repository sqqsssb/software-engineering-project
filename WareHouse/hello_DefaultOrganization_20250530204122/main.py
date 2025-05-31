'''
This is the main application file that creates a GUI to say "Hi".
It uses the tkinter library to create the window and display the message.
'''
import tkinter as tk
from tkinter import messagebox
class MainApp:
    '''
    MainApp class to create the GUI application.
    '''
    def __init__(self, master):
        '''
        Initializes the main window and sets up the GUI components.
        '''
        self.master = master
        master.title("Say Hi Application")
        self.label = tk.Label(master, text="Press the button to say Hi!")
        self.label.pack()
        self.greet_button = tk.Button(master, text="Say Hi", command=self.say_hi)
        self.greet_button.pack()
    def say_hi(self):
        '''
        Displays a message box with "Hi".
        '''
        messagebox.showinfo("Greeting", "Hi")
def main():
    '''
    Entry point of the application.
    '''
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
if __name__ == "__main__":
    main()