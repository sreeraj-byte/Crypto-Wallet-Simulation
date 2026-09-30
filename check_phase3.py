from wallet import Wallet
from transaction import Transaction
from block import Block

alice = Wallet()
tx = Transaction(alice.address, "bob_address", 5, alice.public_key.to_string().hex(), 0)
tx.sign(alice.private_key)

block = Block(1, [tx], "0")
block.mine(3)
print("Mined hash:", block.hash)                                   # starts with 000
print("Nonce tried:", block.nonce)
print("Hash matches:", block.hash == block.compute_hash())         # True

tx.amount = 999
print("After tampering:", block.hash == block.compute_hash())      # False
