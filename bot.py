import telebot
from telebot import types

from config import DATABASE, TOKEN
from logic import DBSupport


if not TOKEN:
    raise ValueError(
        "Bitte tragen Sie den Bot-Token in der Datei config.py ein."
    )


manager = DBSupport(DATABASE)
manager.create_tables()
manager.seed_faq()

bot = telebot.TeleBot(TOKEN)

pending_requests = {}


def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("❓ Häufige Fragen", "📋 Meine Anfragen")
    return keyboard


def request_confirmation_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Anfrage erstellen",
            callback_data="create_request"
        ),
        types.InlineKeyboardButton(
            "❌ Abbrechen",
            callback_data="cancel_request"
        )
    )
    return keyboard


def format_department(department):
    names = {
        "sales": "Verkauf",
        "tech": "Technischer Support",
        "support": "Kundensupport",
        "unknown": "Kundensupport"
    }
    return names.get(department, department)


def format_status(status):
    names = {
        "new": "neu",
        "in_progress": "in Bearbeitung",
        "closed": "geschlossen"
    }
    return names.get(status, status)


@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "Willkommen! 👋\n\n"
        "Ich bin der Support-Bot des Demo-Onlineshops "
        "«Wir verkaufen alles!».\n\n"
        "Schreiben Sie Ihre Frage einfach als normale Nachricht. "
        "Ich suche zuerst nach einer passenden Antwort in der Wissensdatenbank. "
        "Falls keine Lösung gefunden wird, helfe ich Ihnen dabei, "
        "eine Support-Anfrage zu erstellen.",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["help"])
def help_handler(message):
    bot.send_message(
        message.chat.id,
        "Ich helfe bei Fragen zu Bestellungen, Lieferung, Rückgabe, "
        "Zahlung und zur Website.\n\n"
        "Befehle:\n"
        "/start – Hauptmenü öffnen\n"
        "/help – Hilfe anzeigen\n"
        "/my_requests – meine Anfragen anzeigen",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["my_requests"])
def my_requests_handler(message):
    requests = manager.get_user_requests(message.from_user.id)

    if not requests:
        bot.send_message(message.chat.id, "Sie haben noch keine Anfragen.")
        return

    parts = ["📋 Ihre letzten Anfragen:\n"]

    for request in requests[:10]:
        request_id, user_message, department, status, created_at = request
        parts.append(
            f"Anfrage #{request_id}\n"
            f"Abteilung: {format_department(department)}\n"
            f"Status: {format_status(status)}\n"
            f"Nachricht: {user_message}\n"
            f"Datum: {created_at or 'nicht angegeben'}"
        )

    bot.send_message(message.chat.id, "\n\n".join(parts))


@bot.message_handler(
    func=lambda message: message.text == "❓ Häufige Fragen",
    content_types=["text"]
)
def faq_button_handler(message):
    questions = manager.get_faq_questions()
    text = "Häufige Fragen:\n\n" + "\n".join(
        f"• {question}" for question in questions
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(
    func=lambda message: message.text == "📋 Meine Anfragen",
    content_types=["text"]
)
def my_requests_button_handler(message):
    my_requests_handler(message)


@bot.callback_query_handler(
    func=lambda call: call.data in {
        "create_request",
        "cancel_request"
    }
)
def request_callback(call):
    pending = pending_requests.get(call.from_user.id)

    if call.data == "cancel_request":
        pending_requests.pop(call.from_user.id, None)
        bot.edit_message_text(
            "Die Erstellung der Anfrage wurde abgebrochen.",
            call.message.chat.id,
            call.message.message_id
        )
        bot.answer_callback_query(call.id)
        return

    if not pending or not pending.get("message"):
        bot.answer_callback_query(
            call.id,
            "Diese Anfrage ist nicht mehr aktuell. "
            "Bitte senden Sie Ihre Nachricht erneut."
        )
        return

    request_id = manager.add_request(
        user_id=call.from_user.id,
        username=call.from_user.username or "",
        message=pending["message"],
        department=pending["department"]
    )

    pending_requests.pop(call.from_user.id, None)

    bot.edit_message_text(
        f"📝 Die Anfrage wurde erstellt und an den "
        f"{format_department(pending['department'])} weitergeleitet.\n\n"
        f"Anfragenummer: #{request_id}\n"
        f"Den Status können Sie mit /my_requests prüfen.",
        call.message.chat.id,
        call.message.message_id
    )
    bot.answer_callback_query(call.id, "Anfrage erstellt")


@bot.message_handler(
    func=lambda message: (
        message.text
        and message.text.lower().strip() in {
            "menü",
            "menu",
            "hauptmenü",
            "hauptmenu",
            "menü öffnen",
            "menu öffnen",
            "start"
        }
    ),
    content_types=["text"]
)
def menu_handler(message):
    bot.send_message(
        message.chat.id,
        "Hauptmenü:",
        reply_markup=main_menu()
    )


@bot.message_handler(
    func=lambda message: (
        message.text
        and message.text.lower().strip() in {
            "ja",
            "nein",
            "ok",
            "okay",
            "gut",
            "verstanden",
            "danke",
            "alles klar"
        }
    ),
    content_types=["text"]
)
def short_answer_handler(message):
    bot.send_message(
        message.chat.id,
        "Alles klar. Wenn Sie eine Frage haben, schreiben Sie sie einfach hier.",
        reply_markup=main_menu()
    )


@bot.message_handler(content_types=["text"])
def message_handler(message):
    text = (message.text or "").strip()

    if not text:
        bot.send_message(
            message.chat.id,
            "Bitte schreiben Sie Ihre Frage als Textnachricht."
        )
        return

    answer = manager.get_answer(text)

    if answer:
        bot.send_message(
            message.chat.id,
            f"✅ Ich habe eine passende Antwort gefunden:\n\n{answer}",
            reply_markup=main_menu()
        )
        return

    department = manager.detect_department(text)

    pending_requests[message.from_user.id] = {
        "message": text,
        "department": department,
    }

    if department == "unknown":
        pending_requests[message.from_user.id]["department"] = "support"

        bot.send_message(
            message.chat.id,
            "Ich habe keine passende Antwort gefunden.\n\n"
            "Möchten Sie eine Anfrage an den Kundensupport erstellen?",
            reply_markup=request_confirmation_keyboard()
        )
        return

    bot.send_message(
        message.chat.id,
        "Ich habe keine passende Antwort gefunden.\n\n"
        f"Die Frage gehört vermutlich zum Bereich "
        f"{format_department(department)}.\n"
        "Möchten Sie eine Anfrage erstellen?",
        reply_markup=request_confirmation_keyboard()
    )


if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
