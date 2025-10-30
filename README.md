# PW-Manager – Simple CLI Password Manager (offline)

Ein kleiner, rein lokaler Passwort-/Login-Manager für die Konsole.  
Er speichert Einträge verschlüsselt in einer einzigen JSON-Datei und bietet ein simples CLI mit Suchen, Anzeigen, Bearbeiten (im System-Editor) und Löschen.

---

## Features

- 🔐 **Offline & lokal**: Kein Netzwerk, keine Cloud.
- 🔑 **Master-Passwort** zum Entschlüsseln/Schützen des Tresors.
- 📝 **Bearbeiten im Editor** (gesteuert über `EDITOR`).
- 🔎 **Suchen** in Titeln, **Alle Einträge auflisten**, **Einzelne Einträge anzeigen**, **Bearbeiten**, **Hinzufügen**, **Löschen**.
- 🧾 Einträge tragen automatisch **Zeitstempel** (`last_changed_utc`, `last_accessed_utc`) und **Gerätenamen**.

---

## Voraussetzungen

- **Python** ≥ 3.10  
- **[uv](https://docs.astral.sh/uv/)** als Paket-/Umgebungsmanager  
- Vorhandene `pyproject.toml` **und** `uv.lock` aus diesem Repository
- Ein Modul `utils` (liegt im Projekt) mit:
  - `ENCRYPTED_JSON`: Pfad zur verschlüsselten Vault-Datei (z. B. `vault.enc`)
  - `ENTRY_TEMPLATE`: Dict-Vorlage für neue Einträge (mind. `title`, optional `username`, `password`, `notes`, …)
  - `decrypt(path, key) -> str`: entschlüsselt Dateiinhalt und liefert **UTF-8-JSON-String**
  - `encrypt_file_from_json(obj, path, key) -> None`: verschlüsselt `obj` (dict) nach `path`
  - `get_timestamp() -> str`: Zeitstempel in UTC (ISO-8601)

---

## Installation & Setup (empfohlen mit `uv`)

### 1) `uv` installieren

- **macOS / Linux (Shell):**
  ~~~bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ~~~

- **Windows (PowerShell):**
  ~~~powershell
  iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
  ~~~

> Alternative: siehe offizielle `uv`-Dokumentation.

---

### 2) Projekt klonen & Abhängigkeiten synchronisieren

Im Projektordner (der `pyproject.toml` und `uv.lock` enthält):

~~~
uv venv
uv sync --frozen
~~~

- `uv venv` erstellt/aktiviert eine virtuelle Umgebung (standardmäßig `.venv`).
- `uv sync --frozen` installiert **exakt** die Versionen aus `uv.lock`  

> Falls Du bewusst aktualisieren willst:  
> `uv sync` (ohne `--frozen`) respektiert Versionseinschränkungen aus `pyproject.toml` und kann den Lock neu schreiben.

---

### 3) Editor konfigurieren (optional, aber sinnvoll)

PW-Manager öffnet Einträge im Editor aus der Umgebungsvariable `EDITOR`.

- **Linux/macOS (bash/zsh):**
  ~~~bash
  export EDITOR="nano"          # oder "vim", "code -w", etc.
  ~~~

- **Windows (PowerShell – nur aktuelle Session):**
  ~~~powershell
  $env:EDITOR = "notepad"
  ~~~

- **Windows (dauerhaft – Eingabeaufforderung/CMD):**
  ~~~bat
  setx EDITOR notepad
  ~~~

> Für VS Code verwende z. B. `code -w`, damit PW-Manager wartet bis Du den Tab geschlossen hast.

---

## Start

Starte das CLI aus dem Projekt-Root:

~~~
uv run python pw_cli.py
~~~

Beim Start wirst Du nach dem **Master-Passwort** gefragt.  
PW-Manager versucht damit die Datei `utils.ENCRYPTED_JSON` zu entschlüsseln.

---

## CLI-Befehle

Im interaktiven Prompt (`> `) stehen u. a. zur Verfügung:

- `help` – Übersicht anzeigen
- `list` – alle Einträge (Index + Titel)
- `search <term>` – in Titeln suchen (case-insensitive)
- `show <n>` – vollständigen JSON-Eintrag mit Index `n` anzeigen
- `add` – neuen Eintrag auf Basis von `ENTRY_TEMPLATE` anlegen (Editor öffnet sich)
- `edit <n>` – Eintrag `n` im Editor bearbeiten
- `remove <n>` – Eintrag `n` löschen (mit Sicherheitsabfrage)
- `print` – kompletten entschlüsselten Tresor als JSON in der Konsole ausgeben
- `clear` – Konsole leeren
- `exit` / `quit` – beenden

---

## Datenformat

Der Tresor (nach Entschlüsselung) ist ein JSON-Objekt:

~~~json
{
  "logins": [
    {
      "title": "Beispiel",
      "username": "alice",
      "password": "…",
      "notes": "optional",
      "last_changed_utc": "2025-10-30T12:34:56Z",
      "last_accessed_utc": "2025-10-30T12:34:56Z",
      "device_last_accessed": "HOSTNAME"
    }
  ]
}
~~~

**Validierungsregeln beim Speichern:**
- Ein Eintrag **muss** `title` haben **und** (`username` **oder** `notes`) enthalten.
- Zeitstempel & Gerät werden automatisch gesetzt/aktualisiert.

---

## Best Practices & Hinweise

- 🧩 **Backups**: Lege regelmäßige Sicherungen der verschlüsselten Datei an (z. B. Kopie von `vault.enc`).  
- 🔑 **Master-Passwort**: stark wählen und **nicht** wiederverwenden.  
- 🖥️ **Editor-Blockierung**: Nutze Editoren mit „Warten-auf-Schließen“ (z. B. `code -w`), sonst liest das Programm die Datei evtl. zu früh ein.  
- 📁 **Pfad anpassen**: Achte darauf, dass `utils.ENCRYPTED_JSON` auf eine schreibbare Datei/Location zeigt.  
- 🧪 **Erstlauf**: Falls noch keine Vault existiert, sorge dafür, dass `utils.encrypt_file_from_json` initial ein leeres Schema anlegt, z. B. `{"logins": []}`.

---

## Entwicklung

- **Format/Lint/Test** über `uv` (Beispiele):
  ~~~bash
  uv run ruff check
  uv run ruff format
  ~~~

- **Schneller Start im venv**:
  ~~~bash
  source .venv/bin/activate       # Linux/macOS
  .venv\Scripts\activate          # Windows
  python pw_cli.py
  ~~~

---

## Roadmap / TODO (Ideen)

- 🕘 Verlauf/History der Konsolenbefehle (Pfeiltasten)
- 🧰 Automatische zeitgestempelte Backups beim Speichern
- 🧪 Windows-Build/Autostart/Shortcut
- 🔁 Undo/Trash für gelöschte Einträge
- 📦 Export/Import (z. B. CSV/JSON klartext – nur bewusst!)

---

## Sicherheit

Dieses Tool ist **für den persönlichen Gebrauch** gedacht.  
Sorge für:
- eine robuste KDF (z. B. Argon2id), ausreichend Ressourcen, Salt & Authenticated Encryption,
- sicheren Umgang mit dem Master-Passwort,
- physische Sicherheit des Geräts und Backups.

Der Autor übernimmt **keine Haftung** für Datenverlust oder Kompromittierung.