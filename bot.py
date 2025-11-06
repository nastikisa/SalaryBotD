import telebot
from telebot import types
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIG ===
TOKEN = '8289859791:AAHiocOgPA_GuJ2TPxX4n_BN3-SA2RVIps0'
OWNER_ID = 335065525  # your Telegram ID
DEFAULT_PERCENTAGE = 1.3
TAX = 7
AFTER_HOURS_RATE = 75

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Dispatcher Salary Tracker").sheet1

# === Bot Setup ===
bot = telebot.TeleBot(TOKEN)
user_data = {}

# === Start ===
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != OWNER_ID:
        bot.send_message(message.chat.id, "Access denied.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add Load", "🌙 Add After Hours")
    markup.add("💰 Add Cut", "📊 View Monthly Stats")
    markup.add("⚙️ Settings")
    bot.send_message(message.chat.id, "👋 Welcome to Dispatcher Salary Bot!\nChoose an option:", reply_markup=markup)

# === Settings ===
@bot.message_handler(func=lambda m: m.text == "⚙️ Settings")
def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Change Percentage", "⬅️ Back")
    bot.send_message(message.chat.id, "⚙️ Settings Menu:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Change Percentage")
def change_percentage(message):
    bot.send_message(message.chat.id, "Enter new percentage (e.g. 1.4):")
    bot.register_next_step_handler(message, set_percentage)

def set_percentage(message):
    try:
        user_data["percentage"] = float(message.text)
        bot.send_message(message.chat.id, f"✅ Percentage updated to {message.text}%")
    except:
        bot.send_message(message.chat.id, "❌ Invalid number.")

# === Month Selection ===
def ask_month(callback, next_step):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    for i in range(0, len(months), 3):
        markup.row(*months[i:i+3])
    bot.send_message(callback.chat.id, "📅 Select month for this entry:", reply_markup=markup)
    bot.register_next_step_handler(callback, next_step)

# === Add Load ===
@bot.message_handler(func=lambda m: m.text == "➕ Add Load")
def add_load(message):
    bot.send_message(message.chat.id, "Enter gross amount ($):")
    bot.register_next_step_handler(message, process_gross)

def process_gross(message):
    try:
        gross = float(message.text)
        user_data["pending_gross"] = gross
        ask_month(message, finalize_gross)
    except:
        bot.send_message(message.chat.id, "❌ Invalid number.")

def finalize_gross(message):
    month = message.text
    gross = user_data.pop("pending_gross")
    percentage = user_data.get("percentage", DEFAULT_PERCENTAGE)
    salary = gross * (percentage / 100)
    net = salary * (1 - TAX / 100)
    user_data.setdefault("months", {}).setdefault(month, 0)
    user_data["months"][month] += net
    sheet.append_row([str(datetime.now().date()), month, gross, "", "", percentage, TAX, net])
    bot.send_message(message.chat.id,
        f"✅ Load added for {month}:\n"
        f"Gross: ${gross:.2f}\n"
        f"Your percentage: {percentage}%\n"
        f"Earnings before tax: ${salary:.2f}\n"
        f"Tax (7%): -${salary * TAX / 100:.2f}\n"
        f"💵 Net earnings from this load: ${net:.2f}\n\n"
        f"📅 Total for {month}: ${user_data['months'][month]:.2f}"
    )
    notify_owner("Load", month, gross, net)

# === Add After Hours ===
@bot.message_handler(func=lambda m: m.text == "🌙 Add After Hours")
def add_after_hours(message):
    bot.send_message(message.chat.id, "Enter number of shifts:")
    bot.register_next_step_handler(message, process_after_hours)

def process_after_hours(message):
    try:
        shifts = int(message.text)
        user_data["pending_shifts"] = shifts
        ask_month(message, finalize_after_hours)
    except:
        bot.send_message(message.chat.id, "❌ Invalid number.")

def finalize_after_hours(message):
    month = message.text
    shifts = user_data.pop("pending_shifts")
    total = shifts * AFTER_HOURS_RATE
    net = total * (1 - TAX / 100)
    user_data.setdefault("months", {}).setdefault(month, 0)
    user_data["months"][month] += net
    sheet.append_row([str(datetime.now().date()), month, "", shifts, "", "", TAX, net])
    bot.send_message(message.chat.id,
        f"✅ After Hours added for {month}:\n"
        f"Shifts: {shifts}\n"
        f"Total before tax: ${total:.2f}\n"
        f"Tax (7%): -${total * TAX / 100:.2f}\n"
        f"💵 Net earnings: ${net:.2f}\n\n"
        f"📅 Total for {month}: ${user_data['months'][month]:.2f}"
    )
    notify_owner("After Hours", month, total, net)

# === Add Cut ===
@bot.message_handler(func=lambda m: m.text == "💰 Add Cut")
def add_cut(message):
    bot.send_message(message.chat.id, "Enter bonus amount ($):")
    bot.register_next_step_handler(message, process_cut)

def process_cut(message):
    try:
        cut = float(message.text)
        user_data["pending_cut"] = cut
        ask_month(message, finalize_cut)
    except:
        bot.send_message(message.chat.id, "❌ Invalid number.")

def finalize_cut(message):
    month = message.text
    cut = user_data.pop("pending_cut")
    net = cut * (1 - TAX / 100)
    user_data.setdefault("months", {}).setdefault(month, 0)
    user_data["months"][month] += net
    sheet.append_row([str(datetime.now().date()), month, "", "", cut, "", TAX, net])
    bot.send_message(message.chat.id,
        f"✅ Cut added for {month}:\n"
        f"Bonus: ${cut:.2f}\n"
        f"Tax (7%): -${cut * TAX / 100:.2f}\n"
        f"💵 Net earnings: ${net:.2f}\n\n"
        f"📅 Total for {month}: ${user_data['months'][month]:.2f}"
    )
    notify_owner("Cut", month, cut, net)

# === View Monthly Stats ===
@bot.message_handler(func=lambda m: m.text == "📊 View Monthly Stats")
def view_stats(message):
    if "months" not in user_data:
        bot.send_message(message.chat.id, "No data yet.")
        return
    stats = sorted(user_data["months"].items(), key=lambda x: x[1], reverse=True)
    msg = "📊 Monthly Stats:\n"
    for i, (month, total) in enumerate(stats[:3], 1):
        msg += f"{i}. {month}: ${total:.2f}\n"
    bot.send_message(message.chat.id, msg)

# === Notify Owner ===
def notify_owner(entry_type, month, amount, net):
    total = user_data["months"][month]
    bot.send_message(OWNER_ID,
        f"📣 New entry added:\n"
        f"Type: {entry_type}\n"
        f"Month: {month}\n"
        f"Amount: ${amount:.2f}\n"
        f"Net: ${net:.2f}\n"
        f"📅 Total for {month}: ${total:.2f}"
    )

# === Run Bot ===
bot.polling()
