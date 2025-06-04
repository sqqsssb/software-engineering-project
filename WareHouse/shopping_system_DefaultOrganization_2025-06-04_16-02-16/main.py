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