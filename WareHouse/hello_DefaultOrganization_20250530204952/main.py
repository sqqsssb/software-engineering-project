'''
This is the main application file that creates a GUI to display "Hi" when a button is clicked.
'''
import tkinter as tk
class App:
    '''
    Main application class that initializes the GUI components.
    '''
    def __init__(self, root):
        '''
        Initializes the main window and sets up the GUI components.
        '''
        self.root = root
        self.root.title("Say Hi Application")
        # Create a button that calls the say_hi method when clicked
        self.button = tk.Button(root, text="Say Hi", command=self.say_hi)
        self.button.pack(pady=20)
        # Create a label to display the message
        self.label = tk.Label(root, text="")
        self.label.pack(pady=20)
    def say_hi(self):
        '''
        Displays "Hi" in the label when the button is clicked.
        '''
        self.label.config(text="Hi")
def main():
    '''
    Main function to run the application.
    '''
    root = tk.Tk()
    app = App(root)
    root.mainloop()
if __name__ == "__main__":
    main()