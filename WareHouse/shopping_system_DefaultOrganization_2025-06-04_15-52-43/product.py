'''
Manages product-related functionalities such as adding and retrieving products.
'''
class Product:
    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description
    def add_product(self):
        # Logic to add a product to the inventory
        print(f"Product {self.name} added successfully.")
    def get_products(self):
        # Logic to retrieve a list of available products
        print(f"Retrieving product: {self.name} priced at ${self.price:.2f}.")