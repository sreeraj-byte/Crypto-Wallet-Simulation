p = "main.py"
src = open(p).read()

pairs = [
("""    w = Wallet()
    explain("Generated a random private key (ECDSA, curve secp256k1)")
""",
"""    w, phrase = Wallet.create_with_mnemonic()
    explain("Generated 128 bits of secure randomness and turned it into a 12-word recovery phrase")
    explain("Derived the private key from that phrase (ECDSA, curve secp256k1)")
"""),
("""    print(f"Wallet '{name}' created and saved. Address: {w.address}")
""",
"""    print(f"Wallet '{name}' created and saved. Address: {w.address}")
    print("\\n*** RECOVERY PHRASE: write these 12 words on paper and keep them private ***")
    print("   ", phrase)
    print("Anyone with these words can take your coins. It is not saved anywhere.")
    input("Press Enter after you have written it down...")
"""),
("""def toggle_explain():
""",
"""def recover_wallet():
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
"""),
("""9  Toggle explain mode
0  Exit""",
"""9  Toggle explain mode
10 Recover wallet from recovery phrase
0  Exit"""),
(""""7": validate, "8": tamper_demo, "9": toggle_explain}
""",
""""7": validate, "8": tamper_demo, "9": toggle_explain,
           "10": recover_wallet}
"""),
]

for old, new in pairs:
    assert src.count(old) == 1, "Could not find this spot in main.py: " + old[:50]
for old, new in pairs:
    src = src.replace(old, new)
open(p, "w").write(src)
print("main.py updated")
