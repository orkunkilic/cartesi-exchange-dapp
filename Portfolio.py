class Portfolio:
    def __init__(self):
        # Dictionary of user balances. Each user balance is a dictionary that maps token names to balance.
        self.balances = {}

    def update_balance(self, user_id, token, total_change, available_change):
        if user_id not in self.balances:
            self.balances[user_id] = {}

        if token not in self.balances[user_id]:
            self.balances[user_id][token] = {'total': 0, 'available': 0}

        self.balances[user_id][token]['total'] += total_change
        self.balances[user_id][token]['available'] += available_change

    def get_balance(self, user_id, token):
        return self.balances.get(user_id, {}).get(token, None)
