'''
Manages the shopping cart functionalities such as adding, removing products, and checkout.
'''
class Cart:
    def __init__(self):
        self.items = []
    def add_to_cart(self, product):
        self.items.append(product)
        print(f"Added {product.name} to cart.")
    def remove_from_cart(self, product):
        if product in self.items:
            self.items.remove(product)
            print(f"Removed {product.name} from cart.")
        else:
            print(f"Product {product.name} not found in cart.")
    def checkout(self):
        if not self.items:
            print("Cart is empty. Please add products to your cart before checking out.")
            return
        total_price = sum(item.price for item in self.items)
        print(f"Total amount to pay: ${total_price:.2f}")
        # Logic to process the payment can be added here
        self.items.clear()  # Clear the cart after checkout
        print("Checkout successful! Thank you for your purchase.")