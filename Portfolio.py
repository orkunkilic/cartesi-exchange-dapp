from helpers import add_report

class Portfolio:
    def __init__(self):
        # Dictionary of user balances. Each user balance is a dictionary that maps token names to balance.
        self.balances = {}
        self.last_event_id = -1

    def get_last_event_id(self):
        self.last_event_id += 1
        return self.last_event_id

    def update_balance(self, user_id, token, total_change, available_change):
        if user_id not in self.balances:
            self.balances[user_id] = {}

        if token not in self.balances[user_id]:
            self.balances[user_id][token] = {'total': 0, 'available': 0}

        self.balances[user_id][token]['total'] += int(total_change)
        self.balances[user_id][token]['available'] += int(available_change)

        print(self.balances[user_id][token]['total'])
        print(self.balances[user_id][token]['available'])
        add_report({
            "class": "PORTFOLIO",
            "id": self.get_last_event_id(),
            "type": "BALANCE_UPDATED",
            "user": user_id,
            "token": token,
            "total": str(self.balances[user_id][token]['total']),
            "available": str(self.balances[user_id][token]['available'])
        })
    def get_balance(self, user_id, token):
        return self.balances.get(user_id, {}).get(token, None)
