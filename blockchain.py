from block import Block
from transaction import Transaction

class Blockchain:
    def __init__(self, difficulty=3, reward=50):
        self.difficulty = difficulty
        self.reward = reward
        self.chain = [Block(0, [], "0", timestamp=0)]   # genesis block
        self.mempool = []                                # pending transactions

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.receiver == address: balance += tx.amount
                if tx.sender == address:   balance -= tx.amount
        return balance

    def next_nonce(self, address):
        confirmed = sum(1 for b in self.chain for t in b.transactions if t.sender == address)
        pending = sum(1 for t in self.mempool if t.sender == address)
        return confirmed + pending

    def add_transaction(self, tx):
        if tx.sender == "NETWORK":
            raise ValueError("Cannot fake a mining reward")
        if not tx.is_valid():
            raise ValueError("Invalid signature or data")
        if tx.nonce != self.next_nonce(tx.sender):
            raise ValueError("Bad nonce (possible replay)")
        pending_spend = sum(t.amount for t in self.mempool if t.sender == tx.sender)
        if self.get_balance(tx.sender) - pending_spend < tx.amount:
            raise ValueError("Insufficient balance")
        self.mempool.append(tx)

    def mine_pending(self, miner_address):
        reward_tx = Transaction("NETWORK", miner_address, self.reward, "", 0)
        block = Block(len(self.chain), [reward_tx] + self.mempool, self.chain[-1].hash)
        block.mine(self.difficulty)
        self.chain.append(block)
        self.mempool = []

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            cur, prev = self.chain[i], self.chain[i - 1]
            if cur.hash != cur.compute_hash():                     return False
            if cur.previous_hash != prev.hash:                     return False
            if not cur.hash.startswith("0" * self.difficulty):     return False
            if not all(tx.is_valid() for tx in cur.transactions):  return False
        return True
