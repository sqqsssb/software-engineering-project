# EnvironmentDoc 阶段文档

## 结论

 Based on the provided code and the analysis of dependencies, here is the `requirements.txt` file for the online shopping system project:

```plaintext
# requirements.txt
# No external dependencies are required for the current implementation.
# Uncomment the following line if you decide to use any additional libraries in the future.
# sqlite3  # Note: sqlite3 is part of the Python standard library and does not need to be included.

# If you plan to add any additional libraries in the future, you can specify them here.
# For example, if you decide to use Flask for a web interface, you would add:
# Flask>=2.0.0
```

This file indicates that there are currently no external dependencies required for the project to run properly, as the main components are included in Python's standard library. If any additional libraries are introduced later, they can be added to this file accordingly.

## 环境信息

- task: 开发一个在线购物系统
- modality: website
- ideas: 
- language:   Python
- codes: main.py
```python
'''
Main entry point for the Online Shopping Application.
'''
from tkinter import Tk, Label, Button, Entry, StringVar, messagebox
from user import User
from product import Product
from shopping_cart import ShoppingCart
from payment import Payment
from database import Database
class OnlineShoppingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Online Shopping System")
        self.user = User()
        self.cart = ShoppingCart()
        self.database = Database()
        self.payment = Payment()
        self.current_user = None
        self.setup_ui()
    def setup_ui(self):
        self.username_var = StringVar()
        self.password_var = StringVar()
        Label(self.master, text="Username").grid(row=0, column=0)
        Entry(self.master, textvariable=self.username_var).grid(row=0, column=1)
        Label(self.master, text="Password").grid(row=1, column=0)
        Entry(self.master, textvariable=self.password_var, show='*').grid(row=1, column=1)
        Button(self.master, text="Register", command=self.register).grid(row=2, column=0)
        Button(self.master, text="Login", command=self.login).grid(row=2, column=1)
        Button(self.master, text="View Products", command=self.view_products).grid(row=3, column=0, columnspan=2)
        Button(self.master, text="Checkout", command=self.checkout).grid(row=4, column=0, columnspan=2)
    def register(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if username and password:
            if self.user.register(username, password):
                messagebox.showinfo("Success", "User registered successfully!")
            else:
                messagebox.showwarning("Registration Error", "Username already exists.")
        else:
            messagebox.showwarning("Input Error", "Please enter both username and password.")
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if self.user.login(username, password):
            self.current_user = username
            messagebox.showinfo("Success", "Login successful!")
        else:
            messagebox.showwarning("Login Error", "Invalid username or password.")
    def view_products(self):
        products = self.database.get_products()
        product_list = "\n".join([f"{name} - ${price}: {description}" for name, price, description in products])
        messagebox.showinfo("Products", product_list if product_list else "No products available.")
    def checkout(self):
        total_amount = self.cart.calculate_total()
        if total_amount > 0:
            try:
                transaction_id = self.payment.process_payment(total_amount)
                messagebox.showinfo("Payment Successful", f"Your payment was successful! Transaction ID: {transaction_id}")
                self.cart.items.clear()  # Clear the cart after successful payment
            except ValueError as e:
                messagebox.showwarning("Payment Error", str(e))
        else:
            messagebox.showwarning("Cart Empty", "Your shopping cart is empty.")
    def run(self):
        self.master.mainloop()
if __name__ == "__main__":
    root = Tk()
    app = OnlineShoppingApp(root)
    app.run()
```

user.py
```python
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
```

product.py
```python
'''
Product class to represent products in the online store.
'''
class Product:
    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description
```

shopping_cart.py
```python
'''
ShoppingCart class to manage items added to the cart.
'''
class ShoppingCart:
    def __init__(self):
        self.items = []
    def add_item(self, product):
        self.items.append(product)
    def remove_item(self, product):
        self.items.remove(product)
    def calculate_total(self):
        return sum(item.price for item in self.items)
```

payment.py
```python
'''
Payment class to handle payment processing.
'''
import random
class Payment:
    def __init__(self):
        self.transaction_history = []  # To store transaction history
    def process_payment(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        transaction_id = random.randint(1000, 9999)
        print(f"Processing payment of ${amount:.2f}...")
        print(f"Payment successful! Transaction ID: {transaction_id}")
        self.transaction_history.append({
            'transaction_id': transaction_id,
            'amount': amount
        })
        return transaction_id
    def get_transaction_history(self):
        return self.transaction_history
    def refund_payment(self, transaction_id):
        for transaction in self.transaction_history:
            if transaction['transaction_id'] == transaction_id:
                self.transaction_history.remove(transaction)
                print(f"Refund processed for Transaction ID: {transaction_id}")
                return True
        print(f"Transaction ID: {transaction_id} not found for refund.")
        return False
```

database.py
```python
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
```


