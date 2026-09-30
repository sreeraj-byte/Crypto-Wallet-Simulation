from wallet import Wallet
from transaction import Transaction

alice = Wallet()
bob = Wallet()

tx = Transaction(alice.address, bob.address, 5, alice.public_key.to_string().hex(), 0)
tx.sign(alice.private_key)
print("1. Valid after signing:", tx.is_valid())          # expect True

tx.amount = 500
print("2. Valid after tampering:", tx.is_valid())        # expect False

fake = Transaction(alice.address, bob.address, 5, bob.public_key.to_string().hex(), 0)
fake.sign(bob.private_key)
print("3. Forged by Bob:", fake.is_valid())              # expect False

unsigned = Transaction(alice.address, bob.address, 5, alice.public_key.to_string().hex(), 0)
print("4. Unsigned:", unsigned.is_valid())               # expect False
