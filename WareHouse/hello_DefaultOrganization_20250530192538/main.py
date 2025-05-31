'''
Main application file to display a GUI that says "Hi".
'''
import tkinter as tk
from tkinter import messagebox
class MainApp:
    '''
    Main application class for the GUI.
    '''
    def __init__(self, master):
        '''
        Initializes the main window and sets up the GUI components.
        '''
        self.master = master
        master.title("Say Hi App")
        self.label = tk.Label(master, text="Press the button to say Hi!")
        self.label.pack()
        self.say_hi_button = tk.Button(master, text="Say Hi", command=self.say_hi)
        self.say_hi_button.pack()
    def say_hi(self):
        '''
        Displays a message box with "Hi" when the button is clicked.
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