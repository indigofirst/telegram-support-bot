import re
import sqlite3
from datetime import datetime


class DBSupport:
    def __init__(self, database):
        self.database = database

    def get_connection(self):
        return sqlite3.connect(self.database)

    def create_tables(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    keywords TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    message TEXT NOT NULL,
                    department TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TEXT
                )
            """)

            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(requests)").fetchall()
            }

            if "created_at" not in columns:
                conn.execute(
                    "ALTER TABLE requests ADD COLUMN created_at TEXT"
                )

    def seed_faq(self):
        faq_data = [
            (
                "Wie kann ich eine Bestellung aufgeben?",
                "Wählen Sie das gewünschte Produkt aus, klicken Sie auf "
                "«In den Warenkorb» und folgen Sie anschliessend den "
                "Anweisungen im Warenkorb.",
                "bestellung aufgeben,bestellen,warenkorb,kaufen,kauf"
            ),
            (
                "Wie kann ich den Status meiner Bestellung prüfen?",
                "Den Status Ihrer Bestellung finden Sie in Ihrem Kundenkonto "
                "im Bereich «Meine Bestellungen».",
                "bestellstatus,status bestellung,wo ist meine bestellung,"
                "bestellung verfolgen,sendung verfolgen,mein paket"
            ),
            (
                "Wie kann ich meine Bestellung stornieren?",
                "Kontaktieren Sie den Support so schnell wie möglich. "
                "Eine Bestellung kann storniert werden, solange sie noch "
                "nicht versendet wurde.",
                "bestellung stornieren,stornieren,stornierung,"
                "bestellung abbrechen"
            ),
            (
                "Was soll ich tun, wenn ein Produkt beschädigt angekommen ist?",
                "Kontaktieren Sie den Support und senden Sie Fotos des Schadens. "
                "Wir helfen Ihnen bei einem Umtausch oder einer Rückgabe.",
                "beschädigtes produkt,produkt beschädigt,defekt,kaputt,"
                "rückgabe,umtausch"
            ),
            (
                "Wie kann ich den technischen Support kontaktieren?",
                "Beschreiben Sie Ihr Problem direkt in diesem Chat. "
                "Wenn keine passende Antwort gefunden wird, bietet der Bot "
                "die Erstellung einer Support-Anfrage an.",
                "technischer support,support kontaktieren,hilfe,"
                "kundendienst,kundensupport"
            ),
            (
                "Wo finde ich Informationen zur Lieferung?",
                "Informationen zu Lieferarten und Lieferzeiten finden Sie "
                "während des Bestellvorgangs.",
                "lieferung,lieferzeit,versand,versanddauer,"
                "lieferinformationen"
            )
        ]

        for question, answer, keywords in faq_data:
            self.add_faq(question, answer, keywords)

    def add_faq(self, question, answer, keywords):
        with self.get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM faq WHERE question = ?",
                (question,)
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO faq (question, answer, keywords)
                    VALUES (?, ?, ?)
                    """,
                    (question, answer, keywords)
                )
            else:
                conn.execute(
                    """
                    UPDATE faq
                    SET answer = ?, keywords = ?
                    WHERE question = ?
                    """,
                    (answer, keywords, question)
                )

    def get_answer(self, text):

        def normalize(value):
            value = value.lower()
            value = (
                value.replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss")
            )
            value = re.sub(r"[^\w\s]", " ", value)
            return " ".join(value.split())

        normalized_text = normalize(text)
        text_words = set(normalized_text.split())

        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT question, answer, keywords FROM faq"
            ).fetchall()

        matches = []

        for question, answer, keywords in rows:
            normalized_question = normalize(question)

            if normalized_text == normalized_question:
                return answer

            keyword_list = [
                normalize(keyword)
                for keyword in keywords.split(",")
                if keyword.strip()
            ]

            for keyword in keyword_list:
                keyword_words = set(keyword.split())

                if keyword_words and keyword_words.issubset(text_words):
                    matches.append(
                        (
                            len(keyword_words),
                            len(keyword),
                            answer
                        )
                    )

        if not matches:
            return None

        matches.sort(reverse=True)
        return matches[0][2]

    @staticmethod
    def detect_department(text):
        normalized_text = (
            text.lower()
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
        )
        normalized_text = " ".join(normalized_text.split())

        tech_words = [
            "website", "webseite", "fehler", "zahlung", "bezahlen",
            "funktioniert nicht", "haengt", "bug", "anmelden",
            "login", "konto", "passwort", "technisch", "fehlercode"
        ]

        sales_words = [
            "bestellung", "produkt", "lieferung", "versand", "rueckgabe",
            "umtausch", "warenkorb", "verfuegbar", "kaufen", "preis",
            "kosten", "stornieren", "stornierung"
        ]

        tech_score = sum(
            1 for word in tech_words if word in normalized_text
        )
        sales_score = sum(
            1 for word in sales_words if word in normalized_text
        )

        if tech_score > sales_score:
            return "tech"

        if sales_score > tech_score:
            return "sales"

        return "unknown"

    def add_request(self, user_id, username, message, department):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO requests (
                    user_id,
                    username,
                    message,
                    department,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'new', ?)
                """,
                (
                    user_id,
                    username,
                    message,
                    department,
                    created_at
                )
            )

            return cursor.lastrowid

    def get_user_requests(self, user_id):
        with self.get_connection() as conn:
            return conn.execute(
                """
                SELECT id, message, department, status, created_at
                FROM requests
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,)
            ).fetchall()

    def get_faq_questions(self):
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT question FROM faq ORDER BY id"
            ).fetchall()

        return [row[0] for row in rows]
