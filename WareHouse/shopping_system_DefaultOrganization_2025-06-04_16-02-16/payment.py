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