'''
Manages product-related functionalities such as adding, updating, and displaying products.
'''
class ProductManager:
    def __init__(self, database):
        self.database = database
    def add_product(self, product):
        # Logic to add product to the database
        self.database.insert_product(product)
    def get_products(self):
        # Logic to retrieve products from the database
        return self.database.fetch_all_products()