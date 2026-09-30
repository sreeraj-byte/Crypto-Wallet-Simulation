import hashlib
from ecdsa import SigningKey, SECP256k1
from mnemonic import Mnemonic

def pubkey_to_address(pubkey_hex):
    """Address = first 40 chars of SHA-256(public key)."""
    return hashlib.sha256(bytes.fromhex(pubkey_hex)).hexdigest()[:40]

class Wallet:
    def __init__(self, private_key=None):
        # Use a given key (when loading) or generate a fresh random one
        self.private_key = private_key or SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.address = pubkey_to_address(self.public_key.to_string().hex())

    @classmethod
    def from_mnemonic(cls, phrase):
        """Rebuild a wallet from its 12-word recovery phrase."""
        m = Mnemonic("english")
        phrase = " ".join(phrase.lower().split())     # tidy spaces and capitals
        if not m.check(phrase):                       # checks the words and the checksum
            raise ValueError("Invalid recovery phrase")
        seed = m.to_seed(phrase)                      # 64 bytes, always the same for this phrase
        return cls(SigningKey.from_string(seed[:32], curve=SECP256k1))

    @classmethod
    def create_with_mnemonic(cls):
        """Make a new wallet and return it together with its phrase."""
        phrase = Mnemonic("english").generate(strength=128)   # 128 random bits = 12 words
        return cls.from_mnemonic(phrase), phrase
