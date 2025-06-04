'''
ShoppingCart class to manage items in the user's cart.
'''
class ShoppingCart:
    def __init__(self):
        self.items = []
    def add_item(self, product):
        self.items.append(product)
    def remove_item(self, product):
        self.items.remove(product)
    def checkout(self):
        # Logic to process the order
        pass