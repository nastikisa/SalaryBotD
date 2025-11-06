import telebot
from telebot import types
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIG ===
TOKEN = '8289859791:AAHiocOgPA_GuJ2TPxX4n_BN3-SA2RVIps0'
OWNER_ID = 335065525  # твой Telegram ID
DEFAULT_PERCENTAGE = 1.3
DEFAULT_TAX = 7
AFTER_HOURS_RATE = 75

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Dispatcher Salary Tracker").sheet1

# === Bot Setup ===
bot = telebot.TeleBot(TOKEN)

user_data = {}

# === Start Command ===
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

# === Add Load ===
@bot.message_handler(func=lambda m: m.text == "➕ Add Load")
def add_load(message):
    bot.send_message(message.chat.id, "Enter gross amount ($):")
    bot.register_next_step_handler(message, process_gross)

def process_gross(message):
    try:
        gross = float(message.text)
        percentage = user_data.get("percentage", DEFAULT_PERCENTAGE)
        tax = user_data.get("tax", DEFAULT_TAX)
        salary = gross * (percentage / 100)
        salary_after_tax = salary * (1 - tax / 100)
        user_data.setdefault("month_data", []).append(salary_after_tax)
        bot.send_message(message.chat.id, f"✅ Salary from this load: ${salary_after_tax:.2f}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid number. Try again.")

# === Add After Hours ===
@bot.message_handler(func=lambda m: m.text == "🌙 Add After Hours")
def add_after_hours(message):
    bot.send_message(message.chat.id, "Enter number of shifts:")
    bot.register_next_step_handler(message, process_after_hours)

def process_after_hours(message):
    try:
        shifts = int(message.text)
        total = shifts * AFTER_HOURS_RATE
        user_data.setdefault("after_hours", 0)
        user_data["after_hours"] += total
        bot.send_message(message.chat.id, f"✅ Added ${total} from After Hours.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid number. Try again.")

# === Add Cut ===
@bot.message_handler(func=lambda m: m.text == "💰 Add Cut")
def add_cut(message):
    bot.send_message(message.chat.id, "Enter bonus amount ($):")
    bot.register_next_step_handler(message, process_cut)

def process_cut(message):
    try:
        cut = float(message.text)
        user_data.setdefault("cut", 0)
        user_data["cut"] += cut
        bot.send_message(message.chat.id, f"✅ Added ${cut} to Cut.")
    except:
        bot.send_message(message.chat.id, "❌ Invalid number. Try again.")

# === View Stats ===
@bot.message_handler(func=lambda m: m.text == "📊 View Monthly Stats")
def view_stats(message):
    loads_total = sum(user_data.get("month_data", []))
    after_hours = user_data.get("after_hours", 0)
    cut = user_data.get("cut", 0)
    tax = user_data.get("tax", DEFAULT_TAX)
    final_salary = (loads_total + after_hours + cut) * (1 - tax / 100)
    bot.send_message(message.chat.id,
        f"📅 Monthly Stats:\n"
        f"Loads: ${loads_total:.2f}\n"
        f"After Hours: ${after_hours:.2f}\n"
        f"Cut: ${cut:.2f}\n"
        f"Tax: {tax}%\n"
        f"💵 Final Salary: ${final_salary:.2f}"
    )

# === Settings ===
@bot.message_handler(func=lambda m: m.text == "⚙️ Settings")
def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Change Percentage", "Change Tax")
    markup.add("⬅️ Back")
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

@bot.message_handler(func=lambda m: m.text == "Change Tax")
def change_tax(message):
    bot.send_message(message.chat.id, "Enter new tax rate (e.g. 6):")
    bot.register_next_step_handler(message, set_tax)

def set_tax(message):
    try:
        user_data["tax"] = float(message.text)
        bot.send_message(message.chat.id, f"✅ Tax updated to {message.text}%")
    except:
        bot.send_message(message.chat.id, "❌ Invalid number.")

# === Run Bot ===
bot.polling()
