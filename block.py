import json, time, hashlib

class Block:
    def __init__(self, index, transactions, previous_hash, timestamp=None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        data = json.dumps({
            "index": self.index,
            "transactions": [t.hash() for t in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def mine(self, difficulty):
        """Proof-of-work: change nonce until hash starts with N zeros."""
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()
