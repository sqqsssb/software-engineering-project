'''
Main application file that creates a GUI to display "Hi".
'''
import tkinter as tk
class App:
    '''
    Main application class that initializes the GUI.
    '''
    def __init__(self, master):
        '''
        Initializes the main window and sets up the GUI components.
        '''
        self.master = master
        master.title("Say Hi App")
        self.label = tk.Label(master, text="Hi")  # Displays "Hi" in the label
        self.label.pack()
        self.greet_button = tk.Button(master, text="Say Hi", command=self.display_message)
        self.greet_button.pack()
    def display_message(self):
        '''
        Displays the message "Hi" in the label when the button is clicked.
        '''
        self.label.config(text="Hi")
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()