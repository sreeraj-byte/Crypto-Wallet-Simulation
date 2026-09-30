import json
import pytest
from wallet import Wallet
from transaction import Transaction
from blockchain import Blockchain
import storage


def make_tx(w, to, amount, nonce=0):
    tx = Transaction(w.address, to, amount, w.public_key.to_string().hex(), nonce)
    tx.sign(w.private_key)
    return tx


# ---------- Signing and verification ----------

def test_valid_signature():
    assert make_tx(Wallet(), "bob", 5).is_valid()

def test_tampered_amount_rejected():
    tx = make_tx(Wallet(), "bob", 5)
    tx.amount = 500
    assert not tx.is_valid()

def test_forged_signature_rejected():
    alice, bob = Wallet(), Wallet()
    tx = Transaction(alice.address, bob.address, 5, bob.public_key.to_string().hex(), 0)
    tx.sign(bob.private_key)          # Bob signs but claims to be Alice
    assert not tx.is_valid()

def test_unsigned_rejected():
    w = Wallet()
    tx = Transaction(w.address, "bob", 5, w.public_key.to_string().hex(), 0)
    assert not tx.is_valid()

def test_negative_amount_rejected():
    assert not make_tx(Wallet(), "bob", -5).is_valid()


# ---------- Ledger rules ----------

def test_overspend_rejected():
    chain = Blockchain(difficulty=2)
    with pytest.raises(ValueError):
        chain.add_transaction(make_tx(Wallet(), "bob", 5))

def test_replay_rejected():
    alice, bob = Wallet(), Wallet()
    chain = Blockchain(difficulty=2)
    chain.mine_pending(alice.address)
    tx = make_tx(alice, bob.address, 10, chain.next_nonce(alice.address))
    chain.add_transaction(tx)
    chain.mine_pending(alice.address)
    with pytest.raises(ValueError):
        chain.add_transaction(tx)     # same signed transaction again

def test_fake_reward_rejected():
    chain = Blockchain(difficulty=2)
    with pytest.raises(ValueError):
        chain.add_transaction(Transaction("NETWORK", "bob", 1000, "", 0))

def test_balances_after_transfer():
    alice, bob = Wallet(), Wallet()
    chain = Blockchain(difficulty=2)
    chain.mine_pending(alice.address)
    chain.add_transaction(make_tx(alice, bob.address, 10, chain.next_nonce(alice.address)))
    chain.mine_pending(alice.address)
    assert chain.get_balance(alice.address) == 90
    assert chain.get_balance(bob.address) == 10

def test_valid_chain_passes():
    chain = Blockchain(difficulty=2)
    chain.mine_pending(Wallet().address)
    chain.mine_pending(Wallet().address)
    assert chain.is_chain_valid()

def test_tampered_block_detected():
    chain = Blockchain(difficulty=2)
    chain.mine_pending(Wallet().address)
    chain.chain[1].transactions[0].amount = 999
    assert not chain.is_chain_valid()


# ---------- Encrypted wallet storage ----------

def test_wallet_roundtrip(tmp_path):
    path = str(tmp_path / "w.wallet")
    w = Wallet()
    storage.save_wallet(w, "correct-horse", path)
    assert storage.load_wallet("correct-horse", path).address == w.address

def test_wrong_password_rejected(tmp_path):
    path = str(tmp_path / "w.wallet")
    storage.save_wallet(Wallet(), "correct-horse", path)
    with pytest.raises(ValueError):
        storage.load_wallet("wrong-password", path)

def test_ciphertext_differs_each_save(tmp_path):
    w = Wallet()
    p1, p2 = str(tmp_path / "a.wallet"), str(tmp_path / "b.wallet")
    storage.save_wallet(w, "correct-horse", p1)
    storage.save_wallet(w, "correct-horse", p2)
    assert json.load(open(p1))["ciphertext"] != json.load(open(p2))["ciphertext"]


# ---------- Recovery phrase ----------

KNOWN = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

def test_phrase_has_12_words():
    _, phrase = Wallet.create_with_mnemonic()
    assert len(phrase.split()) == 12

def test_phrase_restores_same_wallet():
    w, phrase = Wallet.create_with_mnemonic()
    assert Wallet.from_mnemonic(phrase).address == w.address

def test_same_phrase_gives_same_address():
    assert Wallet.from_mnemonic(KNOWN).address == Wallet.from_mnemonic(KNOWN).address

def test_words_not_in_list_rejected():
    with pytest.raises(ValueError):
        Wallet.from_mnemonic("hello world this is not a real recovery phrase at all nope")

def test_bad_checksum_rejected():
    with pytest.raises(ValueError):
        Wallet.from_mnemonic("abandon " * 11 + "abandon")   # real words, wrong checksum
