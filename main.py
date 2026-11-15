import os
import logging
import threading
import telebot
import google.generativeai as genai

from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN табылмады!")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY табылмады!")

logging.basicConfig(level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN)

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

# ---------------- WEB SERVER ----------------

@app.route("/")
def home():
    return "Exterior Assistant Bot is running!"

@app.route("/health")
def health():
    return {"status": "ok"}

def run_web():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

# ---------------- AI SETTINGS ----------------

SYSTEM_PROMPT = """
Сен Экстерьер көмекшісі атты кәсіби сәулет көмекшісісің.

Сенің міндетің:
- Ғимарат экстерьері туралы кеңес беру;
- Фасад стильдерін түсіндіру;
- Фасад түстерін таңдауға көмектесу;
- Құрылыс материалдарын ұсыну;
- Заманауи сәулет шешімдерін түсіндіру;
- Ғимараттың сыртқы келбетін жобалауға көмектесу.

Барлық жауапты қазақ тілінде бер.
Жауаптарың нақты, түсінікті және пайдалы болсын.
"""

histories = {}

# ---------------- KEYBOARD ----------------

def main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        KeyboardButton("🏛 Экстерьер туралы")
    )

    keyboard.add(
        KeyboardButton("🎨 Фасад түстері"),
        KeyboardButton("🧱 Материалдар")
    )

    keyboard.add(
        KeyboardButton("🏠 Сәулет стильдері")
    )

    keyboard.add(
        KeyboardButton("🗑 Тарихты тазалау")
    )

    return keyboard

# ---------------- START ----------------

@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        "Сәлеметсіз бе! 👋\n\n"
        "Мен — Экстерьер көмекшісімін.\n"
        "Мен ғимарат экстерьері, фасад,"
        " түстер мен материалдар бойынша "
        "көмектесемін.\n\n"
        "Сұрағыңызды жазыңыз немесе төмендегі "
        "батырмаларды пайдаланыңыз.",
        reply_markup=main_keyboard()
    )

# ---------------- HELP ----------------

@bot.message_handler(commands=["help"])
def help_command(message):

    bot.send_message(
        message.chat.id,
        "Қолжетімді командалар:\n\n"
        "/start — Ботты бастау\n"
        "/help — Көмек\n"
        "/clear — Диалог тарихын тазалау"
    )

# ---------------- CLEAR HISTORY ----------------

@bot.message_handler(commands=["clear"])
def clear_history(message):

    histories[message.chat.id] = []

    bot.send_message(
        message.chat.id,
        "Диалог тарихы тазаланды! ✅",
        reply_markup=main_keyboard()
    )

# ---------------- AI ANSWER ----------------

@bot.message_handler(
    content_types=["text"],
    func=lambda message: True
)
def answer(message):

    chat_id = message.chat.id
    question = message.text.strip()

    if question == "🗑 Тарихты тазалау":
        clear_history(message)
        return

    topics = {
        "🏛 Экстерьер туралы":
            "Ғимарат экстерьері туралы толық ақпарат бер.",

        "🎨 Фасад түстері":
            "Ғимарат фасадына түс таңдауға көмектес.",

        "🧱 Материалдар":
            "Экстерьерге арналған құрылыс материалдары туралы айт.",

        "🏠 Сәулет стильдері":
            "Заманауи және классикалық сәулет стильдерін түсіндір."
    }

    question = topics.get(question, question)

    try:

        if chat_id not in histories:
            histories[chat_id] = []

        history = histories[chat_id]

        history.append({
            "role": "user",
            "parts": [SYSTEM_PROMPT + "\n" + question]
        })

        chat = model.start_chat(
            history=history[:-1]
        )

        response = chat.send_message(question)

        answer_text = response.text

        history.append({
            "role": "model",
            "parts": [answer_text]
        })

        # Telegram message limit
        for i in range(0, len(answer_text), 4000):
            bot.send_message(
                chat_id,
                answer_text[i:i + 4000]
            )

    except Exception as error:

        logging.exception("AI ERROR")

        bot.send_message(
            chat_id,
            "Кешіріңіз, жауап алу кезінде қате пайда болды. "
            "Кейінірек қайталап көріңіз."
        )

# ---------------- RUN ----------------

if __name__ == "__main__":

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    logging.info("Exterior Assistant Bot started!")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
