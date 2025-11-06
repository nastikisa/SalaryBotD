message_handler(func=lambda m: m.text == "Change Percentage")
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
