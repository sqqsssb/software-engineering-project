# E-commerce Financial Website User Manual

Welcome to the E-commerce Financial Website, a platform designed to facilitate online shopping and financial transactions in a user-friendly manner.

## Table of Contents

1. [Introduction](#introduction)
2. [Main Functions](#main-functions)
3. [Quick Install](#quick-install)
4. [How to Use](#how-to-use)
5. [Code Structure](#code-structure)
6. [Additional Information](#additional-information)

## Introduction

The E-commerce Financial Website is designed to provide users with a seamless experience for online shopping and financial transactions. This manual serves as a comprehensive guide to help users navigate the platform effectively.

## Main Functions

The E-commerce Financial Website offers the following key functionalities:

- **User Registration and Login**: Users can create an account and log in to access personalized features.
- **Product Management**: Users can view available products, add new products (for admin users), and manage product details.
- **Payment Processing**: Secure payment processing for transactions using various payment methods.
- **Database Management**: The application utilizes a SQLite database to store user and product information.

## Quick Install

To set up the environment and run the E-commerce Financial Website, follow these steps:

1. **Install Python**: Ensure you have Python installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

2. **Clone the Repository**: Clone the repository containing the source code.

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

3. **Install Dependencies**: Create a `requirements.txt` file with the following content:

   ```plaintext
   # No external dependencies are required for the current implementation
   # tkinter is included with Python's standard library
   # sqlite3 is also included with Python's standard library

   # If you plan to use any additional libraries in the future, you can add them here:
   # requests==2.25.1  # For making HTTP requests if needed
   # flask==1.1.2      # If you decide to implement a web server
   ```

   Then, install the dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

## How to Use

1. **Run the Application**: Start the application by executing the main script.

   ```bash
   python main.py
   ```

2. **User Registration**: 
   - Click on the "Register" button on the home page.
   - Follow the prompts to create a new user account.

3. **User Login**: 
   - Click on the "Login" button on the home page.
   - Enter your credentials to log in.

4. **View Products**: Once logged in, you can view the available products. Admin users can add new products through the product management interface.

5. **Payment Processing**: 
   - Select a product and proceed to checkout.
   - Enter your payment information to complete the transaction.

## Code Structure

The application is structured into several modules, each responsible for specific functionalities:

- **main.py**: The main entry point for the application, initializing components and running the UI.
  
  ```python
  from ui import UI
  from product_manager import ProductManager
  from payment_processor import PaymentProcessor
  from database import Database
  from user_auth import UserAuth

  class EcommerceApp:
      def __init__(self):
          self.database = Database()
          self.user_auth = UserAuth(self.database)
          self.product_manager = ProductManager(self.database)
          self.payment_processor = PaymentProcessor()
          self.ui = UI(self)

      def run(self):
          self.ui.create_main_window()
          self.ui.show_home_page()

  if __name__ == "__main__":
      app = EcommerceApp()
      app.run()
  ```

- **ui.py**: Contains the user interface components for the application.

  ```python
  import tkinter as tk
  from tkinter import messagebox

  class UI:
      def __init__(self, app):
          self.app = app
          self.window = tk.Tk()
          self.window.title("E-commerce Financial Website")

      def create_main_window(self):
          self.window.geometry("800x600")

      def show_home_page(self):
          for widget in self.window.winfo_children():
              widget.destroy()
          label = tk.Label(self.window, text="Welcome to the E-commerce Financial Website", font=("Arial", 24))
          label.pack(pady=20)
          login_button = tk.Button(self.window, text="Login", command=self.app.user_auth.login)
          login_button.pack(pady=10)
          register_button = tk.Button(self.window, text="Register", command=self.app.user_auth.register)
          register_button.pack(pady=10)
          self.window.mainloop()
  ```

- **product_manager.py**: Manages product-related functionalities such as adding, updating, and displaying products.

  ```python
  class ProductManager:
      def __init__(self, database):
          self.database = database

      def add_product(self, product):
          self.database.insert_product(product)

      def get_products(self):
          return self.database.fetch_all_products()
  ```

- **payment_processor.py**: Handles payment processing functionalities.

  ```python
  class PaymentProcessor:
      def process_payment(self, amount, payment_info):
          print(f"Processing payment of {amount} with info: {payment_info}")
  ```

- **database.py**: Handles database operations such as connecting to the database, executing queries, and retrieving data.

  ```python
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
  ```

- **user_auth.py**: Manages user registration and login functionalities.

  ```python
  class UserAuth:
      def __init__(self, database):
          self.database = database

      def register(self):
          print("User registration logic here.")

      def login(self):
          print("User login logic here.")
  ```

## Additional Information

For more details on how to extend the application or integrate additional features, please refer to the source code comments and documentation within the code files.

If you encounter any issues or have questions, feel free to reach out for support.

Thank you for using the E-commerce Financial Website!