import json
import os
import socket
import subprocess
import sys
import tempfile
from getpass import getpass
from typing import Tuple
from collections import deque

import utils


def choose_editor():
    """Return the command to open the system editor for a tempfile (list of args)."""
    editor = os.environ.get("EDITOR")
    if editor:
        return editor.split()
    if os.name == "nt":
        # use notepad on Windows
        return ["notepad"]
    # fallback to nano or vi
    for candidate in ("nano", "vi"):
        if shutil_which(candidate):
            return [candidate]
    # final fallback
    return ["vi"]


def shutil_which(cmd):
    """small wrapper to avoid importing shutil everywhere (for compatibility)."""
    import shutil

    return shutil.which(cmd)

def show_entry(entry):
    print(json.dumps(entry, indent=4, ensure_ascii=False))

def open_in_editor_and_read(obj) -> dict:
    """
    Open a temp file containing JSON of `obj` in the user's editor.
    After editor exits, read JSON and return parsed object. Raises ValueError on parse error.
    """
    editor_cmd = os.environ.get("EDITOR")
    if editor_cmd:
        editor = editor_cmd.split()
    else:
        if os.name == "nt":
            editor = ["notepad"]
        else:
            # prefer nano -> vi
            if shutil_which("nano"):
                editor = ["nano"]
            elif shutil_which("vi"):
                editor = ["vi"]
            else:
                editor = ["vi"]

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as tf:
        tf_path = tf.name
        tf.write(json.dumps(obj, indent=4, ensure_ascii=False))
        tf.flush()

    # spawn editor synchronously
    try:
        subprocess.run(editor + [tf_path], check=True)
    except subprocess.CalledProcessError:
        # Editor returned non-zero; still attempt to read file
        pass

    # read back
    try:
        with open(tf_path, "r", encoding="utf-8") as f:
            edited_text = f.read()
        parsed = json.loads(edited_text)
        return parsed
    finally:
        try:
            os.unlink(tf_path)
        except Exception:
            pass


def print_help():
    print(
        """
Available commands:
  search <term>         - search titles for <term> (case-insensitive)
  list                  - list all entries (index + title)
  add                   - add a new entry
  show <n>              - print full JSON for entry n (n from last list/search)
  edit <n>              - edit entry n in your editor (saves in memory; use 'save' to write)
  remove <n>            - removed entry n from the vault
  print                 - dump full decrypted JSON to console
  clear                 - clear output
  help                  - show this help
  exit | quit           - exit
"""
    )

def clear():
    os.system('cls' if os.name=='nt' else 'clear')

class VaultManager:
    def __init__(self):
        self.vault_path = utils.ENCRYPTED_JSON
        self.device_name = socket.gethostname()
        self.decrypt_key = self.query_user_key()
        self.command_buffer = deque(maxlen=50)

        # self.create_backup()  # TODO: With timestamp

        self.run_loop()

    def query_user_key(self) -> str:
        decrypt_key = getpass("Master password: ")

        # Attempt to load/decrypt vault
        try:
            raw = utils.decrypt(self.vault_path, decrypt_key)
            vault = json.loads(raw)
        except ValueError as e:
            print("Failed to open/decrypt vault:", e)
            # Allow one retry
            retry = getpass("Master password (retry): ")
            try:
                vault = json.loads(utils.decrypt(self.vault_path, retry))
                decrypt_key = retry
            except Exception as e2:
                print("Decryption failed again:", e2)
                print("Exiting.")
                sys.exit(1)

        print(f"Vault unlocked with {len(vault.get("logins", []))} entries. Type 'help' for commands.")

        return decrypt_key

    def get_vault(self) -> dict:
        return json.loads(utils.decrypt(self.vault_path, self.decrypt_key))

    def get_logins(self) -> list:
        return self.get_vault().get("logins", [])

    def get_nr_logins(self) -> int:
        return len(self.get_logins())

    def arg_n_valid(self, arg: str) -> Tuple[bool, int]:
        if not arg:
            print("Usage: show <n>")
            return False, -1

        try:
            n = int(arg)
        except ValueError:
            print("Please provide a number from the last search/list.")
            return False, -1

        n_logins = self.get_nr_logins()
        if n_logins < n:
            print(f"Index {n} not valid - There are only {n_logins} entries in the vault.")
            return False, -1

        return True, n

    def list_entries(self):
        for i, e in enumerate(self.get_logins(), start=1):
            title = e.get("title", "<no title>")
            print(f"{i}: {title}")

    def run_loop(self):
        last_search_results = []

        while True:
            print("==========================================================")
            try:
                raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw:
                continue

            parts = raw.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("exit", "quit", "quit()"):
                print("Goodbye.")
                break

            if cmd == "help" or cmd == "help()":
                print_help()
                continue

            if cmd == "clear":
                clear()

            if cmd == "list":
                self.list_entries()
                # Populate last_search_results to reference full list
                last_search_results = [(i, e) for i, e in enumerate(self.get_logins(), start=1)]

                continue

            if cmd == "search":
                if not arg:
                    print("Usage: search <term>")
                    continue
                res = self.search_entries(arg)
                if not res:
                    print("No matches.")
                else:
                    for idx, entry in res:
                        print(f"{idx}: {entry.get('title', '<no title>')}")
                last_search_results = res
                continue

            if cmd == "show":
                valid, n = self.arg_n_valid(arg)
                if not valid:
                    continue

                entry = self.get_logins()[n-1]
                show_entry(entry)
                continue

            if cmd == "remove":
                valid, n = self.arg_n_valid(arg)
                if not valid:
                    continue

                new_vault = self.get_vault()

                deletion_str = f"Proceed with deleting entry {n} \"{new_vault["logins"][n-1]
                                .get("title", "No title found for entry")}\"? [y/n]: "

                del new_vault["logins"][n-1]
                self.save_vault(new_vault, deletion_str=deletion_str)

                continue

            if cmd == "add":
                self.edit_and_write(utils.ENTRY_TEMPLATE)
                continue

            if cmd == "edit":
                if not arg:
                    print("Usage: edit <n>")
                    continue
                try:
                    n = int(arg)
                except ValueError:
                    print("Please provide a number from the last search/list.")
                    continue
                # locate entry index in vault list
                # first try to find in last_search_results
                entry_obj = None
                absolute_index = None
                for i, e in last_search_results:
                    if i == n:
                        absolute_index = i
                        entry_obj = e
                        break
                # fallback: direct index into full list
                if entry_obj is None:
                    if 1 <= n <= self.get_nr_logins():
                        absolute_index = n
                        entry_obj = self.get_logins()[n - 1]
                    else:
                        print("Index not found.")
                        continue

                self.edit_and_write(entry_obj, absolute_index)

            if cmd == "print":
                print(json.dumps(self.get_vault(), indent=4, ensure_ascii=True))
                continue

            print("Unknown command. Type 'help' for a list of commands.")

    def save_vault(self, new_vault: dict, deletion_str: str=""):
        proceed = 'y'

        diff =  self.get_nr_logins() - len(new_vault["logins"])
        if deletion_str == "":
            deletion_str = f"Warning: {diff} entries would be removed. Proceed? [y/n]: "
        if diff > 0:
            proceed = input(deletion_str)
        else:
            print(f"Adding {-diff} entries.")

        if proceed == 'y':
            try:
                utils.encrypt_file_from_json(new_vault, self.vault_path, self.decrypt_key)
                print("Vault saved successfully - Current number of entries: ", self.get_nr_logins())
            except Exception as e:
                print("Failed to save vault:", e)

    def search_entries(self, term):
        term_lower = term.lower()
        results = []
        for i, e in enumerate(self.get_logins(), start=1):
            title = e.get("title", "") or ""
            if term_lower in title.lower():
                results.append((i, e))
        return results

    def edit_and_write(self, entry_obj: dict, absolute_index: int=None):
        new_vault = self.get_vault()

        append = prepend  = False
        if absolute_index is None or absolute_index > self.get_nr_logins():
            append = True
        if absolute_index == -1:
            prepend = True

        # Open entry in editor
        try:
            edited = open_in_editor_and_read(entry_obj)
        except Exception as e:
            print("Failed to parse edited JSON:", e)
            return

        # validate that edited is a dict and has at least a title
        if not isinstance(edited, dict):
            print("Edited content is not a JSON object; aborting.")
            return

        if edited.get("title", "") == "" or (edited.get("username", "") == "" and edited.get("notes", "") == "" ):
            print("Entry must contain title and username or notes.")
            return

        now = utils.get_timestamp()

        if edited != entry_obj:
            edited["last_changed_utc"] = now
        else:
            print("No changes detected.")

        edited["last_accessed_utc"] = now
        edited["device_last_accessed"] = self.device_name

        if append:
            new_vault["logins"].append(edited)
            absolute_index = self.get_nr_logins() + 1
        elif prepend:
            new_vault["logins"] = [edited] + new_vault["logins"]
            absolute_index = 1
        else:
            # Write back into vault (preserve position)
            new_vault["logins"][absolute_index - 1] = edited

        print(f"Entry {absolute_index} written.")

        self.save_vault(new_vault)

        return


if __name__ == "__main__":
    VaultManager()

    # TODO
    #  1. Flush/Clear console history when ending the program?
    #  2. Add Arrow up and down to get prev commands --> command_buffer deque + history command to see command history
    #  3. Github README
    #  4. Binary/autostart/shortcut + Windows test
    #  5. Automatically create backups + print path