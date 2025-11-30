import telebot
import json
from flask import Flask, request
import os
import sys
import requests
import logging

logging.basicConfig(level=logging.INFO)
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    sys.exit("Ошибка: API-токен не задан в переменных окружения")

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот запущен"

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data(as_text=True)
        update = telebot.types.Update.de_json(json_str)
        if update:
            bot.process_new_updates([update])
    except Exception as e:
        app.logger.exception(f"Webhook error: {str(e)}")
    return '', 200

def load_db():
    try:
        with open("db.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_db(data):
    with open("db.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)

    if user_id not in db:
        db[user_id] = {"name": None, "age": None, "money": 10000, "state": "awaiting_name"}
        save_db(db)
        bot.send_message(message.chat.id, "Привет! Как тебя зовут?")
        return


    db[user_id]["money"] = 10000

    keyboard_reply = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    help_button = telebot.types.KeyboardButton("Помощь")
    info_button = telebot.types.KeyboardButton("Инфо")
    about_button = telebot.types.KeyboardButton("О боте")
    link_button = telebot.types.KeyboardButton("Ссылка на чат")
    slot_machine_button = telebot.types.KeyboardButton("Игровой автомат")
    dice_button = telebot.types.KeyboardButton("Игра в кубик")


    keyboard_reply.add(help_button, info_button, about_button, slot_machine_button, link_button, dice_button)

    bot.send_message(message.chat.id, "Hello Bot-World", reply_markup=keyboard_reply)

@bot.message_handler(commands=['help'])
def help_event(message):
    bot.send_message(message.chat.id, "Инструкция по пользованию ботом")

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, "Информация о боте")

@bot.message_handler(content_types=['text'])
def text_event(message):
    user_id = str(message.from_user.id)

    if "awaiting_name" == db.get(user_id, {}).get("state"):
        name = message.text.strip()
        db[user_id]["name"] = name
        db[user_id]["state"] = "awaiting_age"
        save_db(db)
        bot.send_message(message.chat.id, f"Приятно познакомиться, {name}")
        bot.send_message(message.chat.id, "Сколько тебе лет?")
        return
    elif db.get(user_id, {}).get("state") == "awaiting_age":
        try:
            age = int(message.text.strip())
            db[user_id]["age"] = age
            db[user_id]["state"] = None
            save_db(db)
            start(message)
            return
        except ValueError:
            bot.send_message(message.chat.id, "Ты ввел некорректное значение возраста.")
            bot.send_message(message.chat.id, "Сколько тебе лет?")
            return


    if message.text == "Помощь":
        pass
    elif message.text == "Как меня зовут?":
        user_name = db[user_id]["name"]
        bot.send_message(message.chat.id, f"Тебя зовут {user_name}")
    elif message.text == "Инфо":
        pass
    elif message.text == "О боте":
        pass
    elif message.text == "Привет":
        bot.send_message(message.chat.id, "Привет! Чем я могу помочь?")
    elif message.text == "Ссылка на чат":
        bot.send_photo(message.chat.id, open("qr_link.png", 'rb'), "https://t.me/+YwHlJi4_9RRkODli")
    elif message.text == "Игровой автомат":
        if db[user_id]["money"] >= 1000:
            value = bot.send_dice(message.chat.id, emoji='🎰').dice.value

            if value in (1, 22, 43):
                db[user_id]["money"] += 3000
                bot.send_message(message.chat.id, f"Победа! Твой выигрыш составил 3000. Твой баланс: {db[user_id]["money"]}")
            elif value in (16, 32, 48):
                db[user_id]["money"] += 2000
                bot.send_message(message.chat.id, f"Победа! Твой выигрыш составил 2000. Твой баланс: {db[user_id]["money"]}")
            elif value == 64:
                db[user_id]["money"] += 5000
                bot.send_message(message.chat.id, f"Jackpot! Твой выигрыш составил 5000. Твой баланс: {db[user_id]["money"]}")
            else:
                db[user_id]["money"] -= 1000
                bot.send_message(message.chat.id, f"Ты проиграл! Ты потерял 1000. Твой баланс: {db[user_id]["money"]}")
        else:
            bot.send_message(message.chat.id, f"У тебя недостаточно денег на балансе, чтобы начать игру. Нужно как минимум 1000. Твой баланс: {db[user_id]["money"]}")
    elif message.text == "Таблица лидеров":
        leaders = sorted(
            db.items(),
            key=lambda item: item[1]["money"],
            reverse=True
        )

        top5 = leaders[:5]
        text = "ТОП-5 игроков по деньгам:\n\n"

        for position, (user_id, user_data) in enumerate(top5, start=1):
            text+=f"{position}. {user_data['name']} - {user_data['money']} монет\n"

        bot.send_message(message.chat.id, text)
    elif message.text == "Игра в кубик":
        inline_keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)

        btn1 = telebot.types.InlineKeyboardButton("1", callback_data='1')
        btn2 = telebot.types.InlineKeyboardButton("2", callback_data='2')
        btn3 = telebot.types.InlineKeyboardButton("3", callback_data='3')
        btn4 = telebot.types.InlineKeyboardButton("4", callback_data='4')
        btn5 = telebot.types.InlineKeyboardButton("5", callback_data='5')
        btn6 = telebot.types.InlineKeyboardButton("6", callback_data='6')

        inline_keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6)

        bot.send_message(message.chat.id, "Угадай число на кубике", reply_markup=inline_keyboard)

    else:
        bot.send_message(message.chat.id, message.text)

@bot.callback_query_handler(func=lambda call: call.data in ('1', '2', '3', '4', '5', '6'))
def dice_callback(call):
    value = bot.send_dice(call.message.chat.id, emoji='🎲').dice.value
    if str(value) == call.data:
        bot.send_message(call.message.chat.id, "Ты угадал!")
    else:
        bot.send_message(call.message.chat.id, "Попробуй еще раз")

if __name__ == '__main__':
    server_url = os.getenv("RENDER_EXTERNAL_URL")
    if server_url and API_TOKEN:
        webhook_url = f"{server_url.rstrip('/')}/{API_TOKEN}"

        try:
            r = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook",
                             params={"url": webhook_url}, timeout=10)
            logging.info(f"Вебхук установлен: {r.text}")
        except Exception:
            logging.exception("Ошибка при установке webhook")

        port = int(os.getenv("PORT", 10000))
        logging.info(f"Запуск на порте {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        logging.info("Запуск бота в режиме pooling")
        bot.remove_webhook()
        bot.infinity_polling(timeout=60 )