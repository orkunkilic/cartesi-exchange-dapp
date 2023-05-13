import time
import Order
import json
from helpers import add_report

class OrderBook:
    def __init__(self, portfolio):
        self.bids = {}
        self.asks = {}
        self.orders = {}
        self.last_order_id = -1
        self.portfolio = portfolio

        # last_event_id -> not belong to here but convenience > dx :)
        self.last_event_id = -1

    def get_order_id(self):
        self.last_order_id += 1
        return self.last_order_id

    def get_last_event_id(self):
        self.last_event_id += 1
        return self.last_event_id

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
                            executed_quantity = order.quantity
                            new_order.quantity -= order.quantity
                            order.quantity = 0
                            self.remove_order(order)
                        else:
                            executed_quantity = new_order.quantity
                            order.quantity -= new_order.quantity
                            new_order.quantity = 0

                        # Update portfolio
                        self.portfolio.update_balance(new_order.owner, 'bid', -executed_quantity, -executed_quantity)
                        self.portfolio.update_balance(new_order.owner, 'ask', executed_quantity * price, executed_quantity * price)
                        self.portfolio.update_balance(order.owner, 'bid', executed_quantity, executed_quantity)
                        self.portfolio.update_balance(order.owner, 'ask', -executed_quantity * price, -executed_quantity * price)

        elif new_order.type == 'ask':
            for price in sorted(self.bids.keys(), reverse=True):
                if price >= new_order.price:
                    for order in self.bids[price]:
                        if new_order.quantity <= 0:
                            return
                        if new_order.quantity >= order.quantity:
                            executed_quantity = order.quantity
                            new_order.quantity -= order.quantity
                            order.quantity = 0
                            self.remove_order(order)
                        else:
                            executed_quantity = new_order.quantity
                            order.quantity -= new_order.quantity
                            new_order.quantity = 0

                        # Update portfolio
                        self.portfolio.update_balance(new_order.owner, 'bid', executed_quantity, executed_quantity)
                        self.portfolio.update_balance(new_order.owner, 'ask', -executed_quantity * price, -executed_quantity * price)
                        self.portfolio.update_balance(order.owner, 'bid', -executed_quantity, -executed_quantity)
                        self.portfolio.update_balance(order.owner, 'ask', executed_quantity * price, executed_quantity * price)

                    if not self.bids[price]:
                        del self.bids[price]

    def add_order(self, order):
        # When an order is added, reserve the relevant quantity of tokens in the user's portfolio
        if order.type == 'bid':
            self.portfolio.update_balance(order.owner, 'bid', 0, -order.quantity)
        elif order.type == 'ask':
            self.portfolio.update_balance(order.owner, 'ask', 0, -order.quantity * order.price)

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
            add_report({
                "class": "ORDER_BOOK",
                "id": self.get_last_event_id(),
                "type": "ADD_ORDER",
                "order_id": order.id,
                "order_owner": order.owner,
                "order_type": order.type,
                "order_price": order.price,
                "order_quantity": order.quantity
            })
            return order

    def remove_order(self, order):
        # When an order is removed, unreserve the relevant quantity of tokens in the user's portfolio
        if order.type == 'bid':
            self.portfolio.update_balance(order.owner, 'token1', 0, order.quantity)
        elif order.type == 'ask':
            self.portfolio.update_balance(order.owner, 'token2', 0, order.quantity * order.price)

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
        
        add_report({
            "class": "ORDER_BOOK",
            "id": self.get_last_event_id(),
            "type": "REMOVE_ORDER",
            "order_id": order.id,
            "order_owner": order.owner,
            "order_type": order.type,
            "order_price": order.price,
            "order_quantity": order.quantity
        })

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