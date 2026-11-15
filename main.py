import os
import telebot
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# API кілттері
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

histories = {}

SYSTEM_PROMPT = """
Сен Экстерьер көмекшісі атты кәсіби сәулет көмекшісісің.
Пайдаланушыларға ғимарат экстерьері, фасад,
сәулет стильдері, материалдар, түстер,
ландшафт және жобалау туралы қазақ тілінде
нақты әрі түсінікті жауап бер.
"""

@bot.message_handler(commands=["start"])
def start(message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🏛 Экстерьер туралы"))
    keyboard.add(KeyboardButton("🎨 Фасад түстері"))
    keyboard.add(KeyboardButton("🧱 Материалдар"))
    keyboard.add(KeyboardButton("🗑 Тарихты тазалау"))

    bot.send_message(
        message.chat.id,
        "Сәлеметсіз бе! 👋\n"
        "Мен — Экстерьер көмекшісімін.\n"
        "Сәулет және ғимарат экстерьері бойынша "
        "сұрақтарыңызға жауап беремін.",
        reply_markup=keyboard
    )

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "/start — Бастау\n"
        "/help — Көмек\n"
        "/clear — Диалог тарихын тазалау"
    )

@bot.message_handler(commands=["clear"])
def clear_history(message):
    histories[message.chat.id] = []
    bot.send_message(message.chat.id, "Диалог тарихы тазаланды! ✅")

@bot.message_handler(func=lambda message: True)
def answer(message):
    chat_id = message.chat.id
    question = message.text

    if question == "🗑 Тарихты тазалау":
        clear_history(message)
        return

    topics = {
        "🏛 Экстерьер туралы": "Ғимарат экстерьері туралы ақпарат бер.",
        "🎨 Фасад түстері": "Фасадқа түс таңдауға көмектес.",
        "🧱 Материалдар": "Экстерьер материалдары туралы ақпарат бер."
    }

    question = topics.get(question, question)

    try:
        if chat_id not in histories:
            histories[chat_id] = []

        histories[chat_id].append(
            {"role": "user", "parts": [SYSTEM_PROMPT + "\n" + question]}
        )

        chat = model.start_chat(history=histories[chat_id][:-1])
        response = chat.send_message(question)

        histories[chat_id].append(
            {"role": "model", "parts": [response.text]}
        )

        bot.send_message(chat_id, response.text)

    except Exception as e:
        bot.send_message(
            chat_id,
            "Кешіріңіз, қате пайда болды. Кейін қайталап көріңіз."
        )
        print("Қате:", e)

print("Экстерьер көмекшісі іске қосылды!")
bot.infinity_polling(skip_pending=True)
