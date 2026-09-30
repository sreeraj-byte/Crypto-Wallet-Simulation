import json
from wallet import Wallet
import storage

w = Wallet()
storage.save_wallet(w, "correct-horse", "test1.wallet")
print("1. Saved. Address:", w.address)

loaded = storage.load_wallet("correct-horse", "test1.wallet")
print("2. Same address after loading:", loaded.address == w.address)         # True

try:
    storage.load_wallet("wrong-password", "test1.wallet")
    print("3. Wrong password: ACCEPTED (bad)")
except ValueError as e:
    print("3. Wrong password rejected:", e)

storage.save_wallet(w, "correct-horse", "test2.wallet")
a = json.load(open("test1.wallet"))["ciphertext"]
b = json.load(open("test2.wallet"))["ciphertext"]
print("4. Same password and key, different ciphertext:", a != b)             # True

raw_file = open("test1.wallet").read()
print("5. Private key visible in file:", w.private_key.to_string().hex() in raw_file)  # False
