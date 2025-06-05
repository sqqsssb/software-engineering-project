'''
User class to manage user information and authentication.
'''
from database import Database
class User:
    def __init__(self):
        self.username = ""
        self.password = ""
    def register(self, username, password):
        self.username = username
        self.password = password
        db = Database()
        if db.save_user(self):
            return True
        return False
    def login(self, username, password):
        db = Database()
        cursor = db.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        return user is not None