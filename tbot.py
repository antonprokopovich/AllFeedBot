import traceback

from telegram.ext import Updater, CommandHandler, ConversationHandler
from telegram import User, ReplyKeyboardMarkup

bot_token = "623743980:AAG6rmOX9Y47Z3N1qlJ-1scURtVDmMPFWog"
#channel_name = ""
all_networks = ["VK", "YouTube", "Twitter"]

chat_id = None
user_networks = {chat_id:[]}


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
def bot_help(bot, update):
    commands = [
    "/help – получить справку.",
    "/add – добавить социальную сеть.",
    "/del – удалить социальную сеть.",
    ]

    update.message.reply_text("\n".join(commands))

@quiet_exec
def bot_add_network(bot, update):
    global chat_id
    chat_id = update.message.chat.id
    networks_to_add = [
    nw for nw in all_networks if nw not in user_networks.keys()
    ]
    if networks_to_add == []:
        msg = "Все доступные сети уже были добавлены."
        markup = None
    else:
        reply_keyboard = [networks_to_add]
        msg = "Выберите сеть для добавления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)
    return adding()


def bot_del_network(bot, update):
    global chat_id
    chat_id = update.message.chat.id
    if user_networks[chat_id] == []:
        msg = "Список рассылок пуст."
        markup = None
    else:
        reply_keyboard = [[user_networks[chat_id]]]
        msg = "Выберите сеть для удаления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)
    return deleting()

def adding(bot, update):
    chosen_network = update.message.text
    user_networks[user_id].append(chosen_network)
    msg = "Сеть {} добавлена в вашу рассылку.".format(chosen_network)
    bot.message.reply_text(msg)


def deleting(bot, update):
    chosen_network = update.message.text
    user_networks[user_id].remove(chosen_network)
    msg = "Сеть {} удалена из вашей рассылки".format(chosen_network)
    bot.message.reply_text(msg)


if __name__ == "__main__":
    updater = Updater(bot_token)
    updater.dispatcher.add_handler(CommandHandler("help", bot_help))
    updater.dispatcher.add_handler(CommandHandler("add", bot_add_network))


    updater.start_polling()
    updater.idle()







