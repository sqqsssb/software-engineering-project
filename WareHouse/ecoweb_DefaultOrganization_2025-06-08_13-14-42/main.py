'''
Main entry point for the e-commerce financial website application.
'''
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