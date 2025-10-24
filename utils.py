from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import os
import sys
import json

load_dotenv()

encrypted_json_path = os.getenv("ENCRYPTED_JSON")

if not encrypted_json_path:
    print("[!] Environment variable ENCRYPTED_JSON not set in .env file or system env.")
    sys.exit(1)

ENCRYPTED_JSON = Path(encrypted_json_path)

if not ENCRYPTED_JSON.exists():
    print(f"[!] File specified by ENCRYPTED_JSON does not exist: {ENCRYPTED_JSON}")
    sys.exit(1)

ENTRY_TEMPLATE = {
    "title": "",
    "username": "",
    "password": "",
    "notes": "",
}

def get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def xor_encrypt_decrypt(data: bytes, key: bytes | str) -> bytes:
    """Encrypt or decrypt data with XOR using the given key (reversible)."""
    if type(key) is str:
        key = bytes(key, "utf-8")
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def encrypt_file_from_json(input_json: dict, out_path: Path, key: str | bytes):
    """Read JSON, encrypt it, and save to output file."""
    try:
        plaintext = bytes(json.dumps(input_json), "utf-8")
        encrypted = xor_encrypt_decrypt(plaintext, key)
        out_path.write_bytes(encrypted)
        print(f"[+] Encrypted JSON → {out_path}")
    except Exception as e:
        print("Failed to encrypt from JSON:", e)

def encrypt_file_from_file(file_path: Path, out_path: Path, key: str | bytes):
    """Read raw file, encrypt it, and save to output file."""

    if not file_path.exists():
        print(f"[!] {file_path} does not exist. Skipping encryption.")
        return

    try:
        plaintext = file_path.read_bytes()
        encrypted = xor_encrypt_decrypt(plaintext, key)
        out_path.write_bytes(encrypted)
        print(f"[+] Encrypted {file_path} → {out_path}")
    except Exception as e:
        print("Failed to encrypt from file:", e)


def decrypt(file_path, key: str | bytes, verbose: bool=False) -> str:
    """Read words_encrypted.txt, decrypt it, and print the plaintext."""
    if not file_path.exists():
        print(f"[!] {file_path} does not exist.")
        return ""

    encrypted = file_path.read_bytes()
    decrypted = xor_encrypt_decrypt(encrypted, key)
    decoded = decrypted.decode("utf-8")
    if verbose:
        print("Decrypted content:\n")
        print(decoded)

        print("Total nr. of entries: ", len(json.loads(decoded)["logins"]))

    return decoded

def change_key(file_path, old_key, new_key):
    if not file_path.exists():
        print(f"[!] {file_path} does not exist.")
        return

    tmp_file = Path("data/tmp_change_key")

    try:
        decrypted = decrypt(ENCRYPTED_JSON, key=old_key)

        print(f"{decrypted[10:]=}")

        with open(tmp_file, "w") as tf:
            tf.write(decrypted)

        encrypt_file_from_file(tmp_file, file_path, key=new_key)

        decrypted_new = decrypt(file_path, key=new_key)

        print(f"{decrypted_new[10:]=}")

        print(f"Successfully changed encryption of file {file_path}")

    finally:
        os.remove(tmp_file)


if __name__ == "__main__":
    # encrypt_file(PLAINTEXT_FILE, ENCRYPTED_FILE)
    # decrypt(ENCRYPTED_FILE, verbose=True)

    # encrypt_file(PLAINTEXT_JSON, ENCRYPTED_JSON)
    # decrypt(ENCRYPTED_JSON, verbose=True)

    # change_key(ENCRYPTED_JSON, "", "")
    # decrypt(ENCRYPTED_JSON, key="", verbose=True)
    pass
