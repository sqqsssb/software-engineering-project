'''
Handles database operations such as connecting to the database, executing queries, and retrieving data.
'''
import sqlite3
class Database:
    def __init__(self):
        self.connection = sqlite3.connect("ecommerce.db")
        self.create_tables()
    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
        self.connection.commit()
    def insert_product(self, product):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", (product['name'], product['price']))
        self.connection.commit()
    def fetch_all_products(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM products")
        return cursor.fetchall()