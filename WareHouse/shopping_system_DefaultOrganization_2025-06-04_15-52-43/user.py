'''
Handles user-related functionalities such as registration and login.
'''
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def register(self):
        # Logic to register the user
        print(f"User {self.username} registered successfully.")
    def login(self):
        # Logic to authenticate the user
        print(f"User {self.username} logged in successfully.")