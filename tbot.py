# -*- coding: utf-8 -*-
from _thread import start_new_thread
import traceback
import sqlite3

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import User, ReplyKeyboardMarkup, Bot

# Из модуля граббера импортируем функцию граббера для вк.
from grabber import vk_grabber
# Из модуля проверки БД на наличие новых постов импортируем
# основную функцию.
from dbchecker import start_checker

bot_token = "781241991:AAF8n_sfMKiyNlXJ329-D2nRdrTwOURS6GE"
bot = Bot(bot_token)


connection = sqlite3.connect('bot_db.db', check_same_thread=False, timeout=10)
cursor = connection.cursor()

user_id = None
# Позже добавим названия других сетей в список.
all_networks = ["VK"]
# Словарь, который будем преобразовывать в json-формат (строку)
# и добавлять в БД в таблицу users колонку networks в виде 
# {'network_1':{'subscribed':True, 'last_checked': 001}, 'network_2':{'subscribed':False, 'last_checked': 002}}
db_user_networks = {}
# Список сетей для создания кастомной клавиатуры.
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
    # При начале работы с ботом автоматически вызывается команда /start
    # и пользователю присвается user_id.
    global user_id
    user_id = update.message.chat.id
    # Временно зададим единый канал для всех пользователей.
    # Вместо id канала используем @channelusername.
    channel_id = "@feed_channel"

    fname = update.message.from_user.first_name
    if not fname:
        fname = update.message.from_user.username
    msg = "Приветствую, {}!".format(fname)
    msg += "\nДля получения справки воспользуйтесь командой /help"

    update.message.reply_text(msg)
    # При старте работы с ботом заносим id юзера и название канала в БД.
    # Если пользователь повторно воспользовался командой /start,
    # и его данные уже есть в таблице - не меняем их.
    # (IGNORE или REPLACE ?)
    cursor.execute('INSERT or IGNORE INTO users (user_id, channel_id) VALUES (?, ?)', [user_id, channel_id])
    connection.commit()

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

    global user_networks
    # Списки user_networks и networks_to_add являются обратными друг
    # дгуру: добавляя элемент в одну из них, мы убираем его из дургой,
    # и наоборот. 
    user_networks = [
    network for network, value in db_user_networks.items() if value['subscribed'] == True
    ]
    networks_to_add = [
    network for network in all_networks if network not in user_networks
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
    # ??? повторение
    global user_networks 
    user_networks = [
    network for network, value in db_user_networks.items() if value['subscribed'] == True
    ]

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
    global db_user_networks
    global user_id
    global adding
    chosen_network = update.message.text

    if adding:
        db_user_networks[chosen_network] = {'subscribed': True, 'last_checked': 0}
        msg = "Сеть {} добавлена в вашу рассылку.".format(chosen_network)
        msg += "\nДля добавления других сетей, повторно воспользуйтесь командой /add"
        adding = False
        update.message.reply_text(msg)
    else:
        db_user_networks[chosen_network]['subscribed'] = False
        msg = "Сеть {} удалена из вашей рассылки".format(chosen_network)
        msg += "\nДля удаления других сетей, повторно воспользуйтесь командой /del"
        update.message.reply_text(msg)

    #db_user_networks_js = json.dumps(db_user_networks)
    #print((db_user_networks_js))

    # Запрос не записывает новое значение networks в БД.
    # После вызова команды /add юзером и добавления сети VK, значение
    # в колонке networks в таблице users должно стать {'VK': {'subscribed': True, 'last_checked': 0}}
    cursor.execute('UPDATE users SET networks = ? WHERE user_id = ?', [json.dumps(db_user_networks), user_id])
    connection.commit()


if __name__ == "__main__":
    # В отдельных потоках запускаем чеккер БД и граббер ВК.
    start_new_thread(vk_grabber)
    start_new_thread(start_checker, (bot,))

    updater = Updater(bot_token)

    updater.dispatcher.add_handler(CommandHandler("help", bot_help))
    updater.dispatcher.add_handler(CommandHandler("add", bot_add_network))
    updater.dispatcher.add_handler(CommandHandler("del", bot_del_network))
    updater.dispatcher.add_handler(CommandHandler("start", bot_start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, choice_handling))

    updater.start_polling()
    updater.idle()











