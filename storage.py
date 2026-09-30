import os, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag
from ecdsa import SigningKey, SECP256k1
from wallet import Wallet

def _key_from_password(password, salt):
    """Turn a password into a 32-byte encryption key (slow on purpose)."""
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(password.encode())

def save_wallet(wallet, password, path):
    salt, nonce = os.urandom(16), os.urandom(12)      # random every save
    key = _key_from_password(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, wallet.private_key.to_string(), None)
    with open(path, "w") as f:
        json.dump({"salt": salt.hex(), "nonce": nonce.hex(),
                   "ciphertext": ciphertext.hex()}, f)

def load_wallet(password, path):
    with open(path) as f:
        data = json.load(f)
    key = _key_from_password(password, bytes.fromhex(data["salt"]))
    try:
        raw = AESGCM(key).decrypt(bytes.fromhex(data["nonce"]),
                                  bytes.fromhex(data["ciphertext"]), None)
    except InvalidTag:
        raise ValueError("Wrong password or corrupted file")
    return Wallet(SigningKey.from_string(raw, curve=SECP256k1))
