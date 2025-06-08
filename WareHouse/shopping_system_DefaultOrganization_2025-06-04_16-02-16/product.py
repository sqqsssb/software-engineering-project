'''
Product class to represent products in the online store.
'''
class Product:
    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description