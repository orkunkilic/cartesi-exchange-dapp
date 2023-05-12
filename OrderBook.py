import time
import Order

class OrderBook:
    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.orders = {}
        self.last_order_id = -1

    def get_order_id(self):
        self.last_order_id += 1
        return self.last_order_id

    def get_order(self, order_id):
        return self.orders[order_id]

    def match_order(self, new_order):
        if new_order.type == 'bid':
            for price in sorted(self.asks.keys()):
                if price <= new_order.price:
                    for order in self.asks[price]:
                        if new_order.quantity <= 0:
                            return
                        if new_order.quantity >= order.quantity:
                            new_order.quantity -= order.quantity
                            order.quantity = 0
                            self.remove_order(order)
                        else:
                            order.quantity -= new_order.quantity
                            new_order.quantity = 0
                    if not self.asks[price]:
                        del self.asks[price]

        elif new_order.type == 'ask':
            for price in sorted(self.bids.keys(), reverse=True):
                if price >= new_order.price:
                    for order in self.bids[price]:
                        if new_order.quantity <= 0:
                            return
                        if new_order.quantity >= order.quantity:
                            new_order.quantity -= order.quantity
                            order.quantity = 0
                            self.remove_order(order)
                        else:
                            order.quantity -= new_order.quantity
                            new_order.quantity = 0
                    if not self.bids[price]:
                        del self.bids[price]

    def add_order(self, order):
        self.match_order(order)
        if order.quantity > 0:
            if order.type == 'bid':
                if order.price in self.bids:
                    self.bids[order.price].append(order)
                else:
                    self.bids[order.price] = [order]
                self.bids[order.price].sort(key=lambda x: x.timestamp)
            elif order.type == 'ask':
                if order.price in self.asks:
                    self.asks[order.price].append(order)
                else:
                    self.asks[order.price] = [order]
                self.asks[order.price].sort(key=lambda x: x.timestamp)
            
            self.orders[order.id] = order
            return order

    def remove_order(self, order):
        if order.type == 'bid':
            if order in self.bids[order.price]:
                self.bids[order.price].remove(order)
                if not self.bids[order.price]:
                    del self.bids[order.price]
        elif order.type == 'ask':
            if order in self.asks[order.price]:
                self.asks[order.price].remove(order)
                if not self.asks[order.price]:
                    del self.asks[order.price]

    def cancel_order(self, id):
        for price in self.bids.keys():
            for order in self.bids[price]:
                if order.id == id:
                    self.remove_order(order)
                    return True
        for price in self.asks.keys():
            for order in self.asks[price]:
                if order.id == id:
                    self.remove_order(order)
                    return True
        
        return False
                    
    def view_book(self):
            print('Bids:')
            for price in sorted(self.bids.keys(), reverse=True):
                for order in self.bids[price]:
                    print('Owner:', order.owner, 'Price:', order.price, 'Quantity:', order.quantity, 'Time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order.timestamp)))
            print('Asks:')
            for price in sorted(self.asks.keys()):
                for order in self.asks[price]:
                    print('Owner:', order.owner, 'Price:', order.price, 'Quantity:', order.quantity, 'Time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order.timestamp)))