'''
Handles database interactions for user and product management.
'''
class Database:
    def __init__(self):
        # Initialize database connection
        print("Database connection initialized.")
    def create_tables(self):
        # Logic to create necessary tables in the database
        print("Database tables created.")
    def insert_user(self, user):
        # Logic to insert a new user into the database
        print(f"User {user.username} inserted into the database.")
    def insert_product(self, product):
        # Logic to insert a new product into the database
        print(f"Product {product.name} inserted into the database.")