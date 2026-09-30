import json, time, hashlib
from ecdsa import VerifyingKey, SECP256k1, BadSignatureError
from wallet import pubkey_to_address

class Transaction:
    def __init__(self, sender, receiver, amount, public_key, nonce, timestamp=None):
        self.sender = sender          # sender's address
        self.receiver = receiver
        self.amount = amount
        self.public_key = public_key  # hex, needed so others can verify
        self.nonce = nonce            # counter, stops replay attacks
        self.timestamp = timestamp or time.time()
        self.signature = None

    def payload(self):
        """The exact data that gets signed."""
        return json.dumps({
            "sender": self.sender, "receiver": self.receiver,
            "amount": self.amount, "nonce": self.nonce,
            "timestamp": self.timestamp}, sort_keys=True).encode()

    def hash(self):
        return hashlib.sha256(self.payload()).hexdigest()

    def sign(self, private_key):
        self.signature = private_key.sign(self.payload(), hashfunc=hashlib.sha256).hex()

    def is_valid(self):
        if self.sender == "NETWORK":          # mining reward, no signature
            return True
        if not self.signature or self.amount <= 0:
            return False
        # The public key must really belong to the sender's address
        if pubkey_to_address(self.public_key) != self.sender:
            return False
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(self.public_key), curve=SECP256k1)
            return vk.verify(bytes.fromhex(self.signature), self.payload(),
                             hashfunc=hashlib.sha256)
        except (BadSignatureError, ValueError):
            return False