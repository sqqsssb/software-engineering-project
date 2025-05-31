'''
This is the main file for the Hi application.
It creates a simple GUI that displays "Hi" when a button is clicked.
'''
import tkinter as tk
from tkinter import messagebox
class MainApp:
    '''
    Main application class that initializes the GUI.
    '''
    def __init__(self, master):
        '''
        Initializes the main window and its components.
        '''
        self.master = master
        master.title("Say Hi Application")
        self.label = tk.Label(master, text="Click the button below to see a greeting!")
        self.label.pack()
        self.say_hi_button = tk.Button(master, text="Say Hi", command=self.say_hi)
        self.say_hi_button.pack()
    def say_hi(self):
        '''
        Displays a message box with "Hi".
        '''
        messagebox.showinfo("Greeting", "Hi")
def main():
    '''
    Main function to run the application.
    '''
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
if __name__ == "__main__":
    main()