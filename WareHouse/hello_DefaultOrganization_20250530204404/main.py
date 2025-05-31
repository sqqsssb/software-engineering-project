'''
This is a simple GUI application that displays "Hi" when a button is pressed.
'''
import tkinter as tk
class MainApp:
    '''
    Main application class that creates the GUI.
    '''
    def __init__(self, master):
        '''
        Initializes the main window and its components.
        '''
        self.master = master
        master.title("Say Hi Application")
        self.label = tk.Label(master, text="Click the button below to display 'Hi':")  # Revised label text for clarity
        self.label.pack()
        self.greet_button = tk.Button(master, text="Say Hi", command=self.say_hi)
        self.greet_button.pack()
        self.output_label = tk.Label(master, text="")
        self.output_label.pack()
    def say_hi(self):
        '''
        Displays "Hi" in the output label when the button is pressed.
        '''
        self.output_label.config(text="Hi")
def main():
    '''
    Main function to run the application.
    '''
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
if __name__ == "__main__":
    main()