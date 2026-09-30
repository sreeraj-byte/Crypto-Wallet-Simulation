import os
from getpass import getpass
from wallet import Wallet
from transaction import Transaction
from blockchain import Blockchain
import storage

WALLET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wallets")
os.makedirs(WALLET_DIR, exist_ok=True)

EXPLAIN = True
chain = Blockchain(difficulty=3)
wallets = {}          # name -> unlocked Wallet (kept in memory only)


def explain(msg):
    if EXPLAIN:
        print("   [step]", msg)


def wallet_path(name):
    return os.path.join(WALLET_DIR, name + ".wallet")


def valid_name(name):
    return bool(name) and name.replace("_", "").isalnum()


def label(address):
    for name, w in wallets.items():
        if w.address == address:
            return name
    return address[:10] + "..."


def pick_wallet(prompt):
    if not wallets:
        print("No wallet loaded. Create or load one first.")
        return None
    print("Loaded wallets:", ", ".join(wallets))
    name = input(prompt).strip()
    if name not in wallets:
        print("Unknown wallet name.")
        return None
    return name


def create_wallet():
    name = input("New wallet name (letters, numbers, _): ").strip()
    if not valid_name(name):
        print("Invalid name.")
        return
    if name in wallets or os.path.exists(wallet_path(name)):
        print("A wallet with that name already exists.")
        return
    password = getpass("Set password (typing is hidden): ")
    if len(password) < 6:
        print("Password must be at least 6 characters.")
        return
    if password != getpass("Confirm password: "):
        print("Passwords do not match.")
        return
    w, phrase = Wallet.create_with_mnemonic()
    explain("Generated 128 bits of secure randomness and turned it into a 12-word recovery phrase")
    explain("Derived the private key from that phrase (ECDSA, curve secp256k1)")
    explain("Derived the public key, then address = SHA-256(public key)[:40]")
    storage.save_wallet(w, password, wallet_path(name))
    explain("Encrypted the private key with AES-GCM; key made from the password with scrypt + random salt")
    wallets[name] = w
    print(f"Wallet '{name}' created and saved. Address: {w.address}")
    print("\n*** RECOVERY PHRASE: write these 12 words on paper and keep them private ***")
    print("   ", phrase)
    print("Anyone with these words can take your coins. It is not saved anywhere.")
    input("Press Enter after you have written it down...")


def load_existing():
    saved = sorted(f[:-7] for f in os.listdir(WALLET_DIR) if f.endswith(".wallet"))
    if not saved:
        print("No saved wallets yet. Create one first.")
        return
    print("Saved wallets:", ", ".join(saved))
    name = input("Wallet name to load: ").strip()
    if name not in saved:
        print("No such wallet file.")
        return
    try:
        w = storage.load_wallet(getpass("Password: "), wallet_path(name))
    except ValueError as e:
        print("Failed:", e)
        return
    explain("Rebuilt the key from your password + the salt stored in the file, then decrypted the private key")
    wallets[name] = w
    print(f"Loaded '{name}'. Address: {w.address}")


def send_coins():
    sender_name = pick_wallet("From wallet: ")
    if not sender_name:
        return
    sender = wallets[sender_name]
    target = input("To (wallet name or 40-character address): ").strip()
    receiver = wallets[target].address if target in wallets else target
    if len(receiver) != 40 or any(c not in "0123456789abcdef" for c in receiver):
        print("Invalid receiver.")
        return
    try:
        amount = int(input("Amount (whole coins): "))
    except ValueError:
        print("Amount must be a whole number.")
        return
    if amount <= 0:
        print("Amount must be positive.")
        return
    tx = Transaction(sender.address, receiver, amount,
                     sender.public_key.to_string().hex(),
                     chain.next_nonce(sender.address))
    explain(f"Created transaction: {sender_name} -> {label(receiver)}, amount {amount}, nonce {tx.nonce}")
    explain(f"Hashed the transaction data with SHA-256: {tx.hash()[:16]}...")
    tx.sign(sender.private_key)
    explain(f"Signed the data with {sender_name}'s private key: {tx.signature[:16]}...")
    try:
        chain.add_transaction(tx)
    except ValueError as e:
        print("Rejected:", e)
        return
    explain("Checked signature, address match, nonce (replay protection) and balance: all OK")
    explain("Added to the mempool (waiting for a miner)")
    print("Transaction accepted. Mine a block to confirm it.")


def mine():
    name = pick_wallet("Miner wallet (receives the reward): ")
    if not name:
        return
    explain(f"Collecting {len(chain.mempool)} pending transaction(s) from the mempool")
    explain(f"Adding a {chain.reward}-coin reward for the miner")
    explain(f"Proof-of-work: searching for a hash starting with {'0' * chain.difficulty}")
    chain.mine_pending(wallets[name].address)
    block = chain.chain[-1]
    explain(f"Found nonce {block.nonce}, block hash {block.hash[:16]}...")
    print(f"Block {block.index} mined. Chain length: {len(chain.chain)}")


def balances():
    if not wallets:
        print("No wallet loaded.")
        return
    for name, w in wallets.items():
        print(f"  {name:<12} {w.address}   balance: {chain.get_balance(w.address)}")
    print("  Pending in mempool:", len(chain.mempool))


def history():
    name = pick_wallet("Wallet name: ")
    if not name:
        return
    addr = wallets[name].address
    print(f"\nHistory for {name}:")
    found = False
    for block in chain.chain:
        for tx in block.transactions:
            if tx.sender == addr or tx.receiver == addr:
                found = True
                if tx.sender == "NETWORK":
                    desc = f"+{tx.amount} mining reward"
                elif tx.sender == addr:
                    desc = f"-{tx.amount} sent to {label(tx.receiver)}"
                else:
                    desc = f"+{tx.amount} received from {label(tx.sender)}"
                print(f"  Block {block.index}: {desc}")
    for tx in chain.mempool:
        if tx.sender == addr or tx.receiver == addr:
            found = True
            print(f"  Pending: {tx.amount} ({label(tx.sender)} -> {label(tx.receiver)})")
    if not found:
        print("  No transactions yet.")


def validate():
    explain("Re-checking every block: hash matches contents, links to previous hash, proof-of-work, signatures")
    print("Chain valid?", chain.is_chain_valid())


def tamper_demo():
    if len(chain.chain) < 2:
        print("Mine at least one block first.")
        return
    tx = chain.chain[1].transactions[0]
    original = tx.amount
    print("Chain valid before tampering?", chain.is_chain_valid())
    tx.amount = 9999
    print(f"Changed an amount in block 1 from {original} to 9999...")
    explain("The transaction hash changed, so the block hash no longer matches its contents")
    print("Chain valid after tampering?", chain.is_chain_valid())
    tx.amount = original
    print("Amount restored. Chain valid again?", chain.is_chain_valid())


def recover_wallet():
    name = input("Name for the recovered wallet: ").strip()
    if not valid_name(name):
        print("Invalid name.")
        return
    if name in wallets or os.path.exists(wallet_path(name)):
        print("A wallet with that name already exists.")
        return
    phrase = input("Enter your 12-word recovery phrase: ")
    try:
        w = Wallet.from_mnemonic(phrase)
    except ValueError as e:
        print("Failed:", e)
        return
    explain("Checked the phrase checksum, then rebuilt the same private key from it")
    password = getpass("Set a new password (typing is hidden): ")
    if len(password) < 6:
        print("Password must be at least 6 characters.")
        return
    if password != getpass("Confirm password: "):
        print("Passwords do not match.")
        return
    storage.save_wallet(w, password, wallet_path(name))
    explain("Encrypted the recovered key with the new password and saved it")
    wallets[name] = w
    print(f"Wallet '{name}' recovered. Address: {w.address}")


def toggle_explain():
    global EXPLAIN
    EXPLAIN = not EXPLAIN
    print("Explain mode:", "ON" if EXPLAIN else "OFF")


MENU = """
=== Crypto Wallet Simulation ===
1  Create wallet
2  Load saved wallet
3  Send coins
4  Mine pending transactions
5  Show balances
6  Transaction history
7  Validate blockchain
8  Tamper demo
9  Toggle explain mode
10 Recover wallet from recovery phrase
0  Exit
"""

ACTIONS = {"1": create_wallet, "2": load_existing, "3": send_coins,
           "4": mine, "5": balances, "6": history,
           "7": validate, "8": tamper_demo, "9": toggle_explain,
           "10": recover_wallet}


def main():
    while True:
        print(MENU)
        choice = input("Choice: ").strip()
        if choice == "0":
            print("Goodbye.")
            break
        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
