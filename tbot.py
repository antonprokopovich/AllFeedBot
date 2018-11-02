import traceback

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import User, ReplyKeyboardMarkup

import sqlite3

connection = sqlite3.connect('bot_db.db')
cur = connection.cursor()

bot_token = "781241991:AAF8n_sfMKiyNlXJ329-D2nRdrTwOURS6GE"

all_networks = ["VK", "YouTube", "Twitter"]
user_networks = []


def quiet_exec(f):
    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except BaseException as e:
            e = "Error in {}(): {}\n{}".format(
                f.__name__, str(e), traceback.format_exc()
            )
            print(e)
    return wrapper

@quiet_exec 
def bot_start(bot, update):
    global chat_id
    chat_id = update.message.chat.id

    fname = update.message.from_user.first_name
    if not fname:
        fname = update.message.from_user.username
    msg = "Приветствую, {}!".format(fname)
    msg += "\nДля получения справки воспользуйтесь командой /help"

    update.message.reply_text(msg)

@quiet_exec   
def bot_help(bot, update):
    commands = [
    "/help – получить справку.",
    "/add – добавить социальную сеть.",
    "/del – удалить социальную сеть.",
    ]

    update.message.reply_text("\n".join(commands))

adding = False
@quiet_exec
def bot_add_network(bot, update):
    global adding
    adding = True

    networks_to_add = [
    nw for nw in all_networks if nw not in user_networks
    ]
    if networks_to_add == []:
        msg = "Все доступные сети уже были добавлены."
        markup = None
        adding =False
    else:
        reply_keyboard = [networks_to_add]
        msg = "Выберите сеть для добавления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)

@quiet_exec
def bot_del_network(bot, update):
    global adding
    adding = False

    if user_networks == []:
        msg = "Список рассылок пуст."
        markup = None
    else:
        reply_keyboard = [user_networks]
        msg = "Выберите сеть для удаления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)

@quiet_exec
def choice_handling(bot, update):
    global adding
    if adding:
        chosen_network = update.message.text
        user_networks.append(chosen_network)
        msg = "Сеть {} добавлена в вашу рассылку.".format(chosen_network)
        msg += "\nДля добавления других сетей повторно воспользуйтесь командой /add"
        adding = False
        update.message.reply_text(msg)
    else:
        chosen_network = update.message.text
        user_networks.remove(chosen_network)
        msg = "Сеть {} удалена из вашей рассылки".format(chosen_network)
        msg += "\nДля удаления других сетей повторно воспользуйтесь командой /del"
        update.message.reply_text(msg)


if __name__ == "__main__":
    updater = Updater(bot_token)

    updater.dispatcher.add_handler(CommandHandler("help", bot_help))
    updater.dispatcher.add_handler(CommandHandler("add", bot_add_network))
    updater.dispatcher.add_handler(CommandHandler("del", bot_del_network))
    updater.dispatcher.add_handler(CommandHandler("start", bot_start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, choice_handling))


    updater.start_polling()
    updater.idle()

    









