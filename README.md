# Telegram Support Bot

Ein Telegram-Bot in Python, der häufige Supportfragen beantwortet und bei Bedarf Support-Anfragen in SQLite speichert.

## Funktionen

- FAQ-Suche mit normalisierten Benutzereingaben
- Erkennung typischer Schreibvarianten und deutscher Umlaute
- automatische Zuordnung zu Verkauf oder technischem Support
- Erstellung einer Anfrage nach Bestätigung durch den Benutzer
- Speicherung und Anzeige eigener Support-Anfragen
- getrennte Daten pro Telegram-Benutzer
- Reply- und Inline-Buttons

## Technologien

- Python 3.10+
- pyTelegramBotAPI
- SQLite / SQL
- reguläre Ausdrücke

## Projektstruktur

```text
telegram-support-bot/
├── .gitignore
├── bot.py
├── config.py
├── logic.py
├── README.md
├── requirements.txt
└── support.db
```

`support.db` und die benötigten Tabellen werden beim ersten Start automatisch erstellt.

## Installation

```bash
pip install -r requirements.txt
```

Telegram-Bot über BotFather erstellen und den Token in `config.py` eintragen:

```python
TOKEN = "DEIN_BOT_TOKEN"
```

Bot starten:

```bash
python bot.py
```

## Befehle

- `/start` – Hauptmenü öffnen
- `/help` – Hilfe anzeigen
- `/my_requests` – eigene Support-Anfragen anzeigen

## Technische Details

- FAQ-Fragen werden zuerst direkt und danach über Schlüsselwörter verglichen.
- Satzzeichen und Schreibvarianten beeinflussen die Suche möglichst wenig.
- SQL-Abfragen verwenden Parameter-Platzhalter.
- Abteilung, Status und Erstellungszeit einer Anfrage werden in SQLite gespeichert.
- Noch nicht bestätigte Anfragen werden vorübergehend im Arbeitsspeicher gehalten.

## Einschränkungen

- Die FAQ-Suche ist regelbasiert und verwendet kein Sprachmodell.
- Nicht bestätigte Anfragen gehen bei einem Neustart verloren.
- Das Projekt ist als lokales Portfolio-Projekt ausgelegt.

## Sicherheit

Ein echter Telegram-Bot-Token gehört nicht in ein öffentliches Repository. Vor dem Hochladen sollte `TOKEN` in `config.py` leer sein oder einen Platzhalter enthalten.
