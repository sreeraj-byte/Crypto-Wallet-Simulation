from wallet import Wallet
from transaction import Transaction
from blockchain import Blockchain

def make_tx(w, to, amount, nonce):
    tx = Transaction(w.address, to, amount, w.public_key.to_string().hex(), nonce)
    tx.sign(w.private_key)
    return tx

alice, bob = Wallet(), Wallet()
chain = Blockchain(difficulty=2)

chain.mine_pending(alice.address)
print("1. Alice balance after mining:", chain.get_balance(alice.address))      # 50

tx = make_tx(alice, bob.address, 10, chain.next_nonce(alice.address))
chain.add_transaction(tx)
print("2. Mempool size:", len(chain.mempool))                                  # 1

chain.mine_pending(alice.address)
print("3. Alice:", chain.get_balance(alice.address),
      "Bob:", chain.get_balance(bob.address))                                  # 90, 10

try:
    chain.add_transaction(make_tx(bob, alice.address, 500, chain.next_nonce(bob.address)))
    print("4. Overspend: ACCEPTED (bad)")
except ValueError as e:
    print("4. Overspend rejected:", e)

try:
    chain.add_transaction(tx)
    print("5. Replay: ACCEPTED (bad)")
except ValueError as e:
    print("5. Replay rejected:", e)

print("6. Chain valid:", chain.is_chain_valid())                               # True
chain.chain[2].transactions[1].amount = 999
print("7. Valid after tampering:", chain.is_chain_valid())                     # False
