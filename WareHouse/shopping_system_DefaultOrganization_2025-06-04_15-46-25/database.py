'''
Database class to handle database connections and queries.
'''
import sqlite3
class Database:
    def connect(self):
        # Logic to connect to the database
        self.connection = sqlite3.connect('shopping.db')
    def execute_query(self, query):
        # Logic to execute SQL queries
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()