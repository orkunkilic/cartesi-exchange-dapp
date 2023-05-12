import time

class Order:
    def __init__(self, id, owner, type, price, quantity):
        self.id = id
        self.owner = owner
        self.type = type
        self.price = price
        self.quantity = quantity
        self.timestamp = time.time()