'''
Database class to manage database connections and operations.
'''
import sqlite3
class Database:
    def __init__(self):
        self.connection = sqlite3.connect('shopping.db')
        self.create_tables()
    def create_tables(self):
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price REAL,
                    description TEXT
                )
            ''')
    def save_user(self, user):
        try:
            with self.connection:
                self.connection.execute('''
                    INSERT INTO users (username, password) VALUES (?, ?)
                ''', (user.username, user.password))
            return True
        except sqlite3.IntegrityError:
            return False
    def get_products(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT name, price, description FROM products')
        return cursor.fetchall()
    def close(self):
        self.connection.close()