# -*- coding: utf-8 -*-
from _thread import start_new_thread
import traceback
import sqlite3

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import User, ReplyKeyboardMarkup, Bot

# Из модуля граббера импортируем функцию граббера для вк.
from vk_grabber import vk_grabber
# Из модуля проверки БД на наличие новых постов импортируем
# основную функцию.
from dbchecker import start_checker
from youtube_grabber import get_authenticated_service


bot_token = "781241991:AAF8n_sfMKiyNlXJ329-D2nRdrTwOURS6GE"
bot = Bot(bot_token)

connection = sqlite3.connect('bot_db.db', check_same_thread=False, timeout=10)
cursor = connection.cursor()

# Телеграм-id пользователя будет инициализирован при первом обращении
# к боту, когда отправляется команда /start.
user_id = None

# Позже добавим названия других сетей в список.
all_networks = ["VK", "YouTube"]
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
    """
    Хэндлер команды /start, которая отправляется от пользователя боту
    автоматически при отправке 
    """
    # При начале работы с ботом автоматически вызывается команда /start
    # и пользователю присвается user_id, под которым он заносится в БД.
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

# Флаг, который будет использоваться для перехода в режим удаления
# или добавления соц. сетей, чтобы хэндлер choice_handling(),
# обрабатывающий сообщение с название соц. сети, определял
# удалять или добавлять его в соответствии текущем режимом.
adding = False
@quiet_exec
def bot_add_network(bot, update):
    """ Хэндлер обрабатывающий команду /add и предоставляющий
    пользователю варианты доступных для добавления социальных сетей."""
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
        adding = False
    else:
        reply_keyboard = [networks_to_add]
        msg = "Выберите сеть для добавления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)

@quiet_exec
def bot_del_network(bot, update):
    """Обрабатывает команду /del и предоставляющий
    пользователю варианты доступных для добавления социальных сетей."""
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
    """Хэндлер срабатывающий после того, как пользователь выбрал сеть
    для добавления/удаления, и обновляющий список рассылок db_user_networks.
    """
    global db_user_networks
    global adding
    global user_id

    user_id = update.message.chat.id
    chosen_network = update.message.text

    if adding:

        if chosen_network.lower() == 'youtube':
            """
            Если добавлена сеть YouTube, то будет выполняться протокол OAuth,
            по которому бот отправит пользователю ссылку на авторизацию,
            пройдя по которой пользователь передаст боту права на чтение данных
            его youtube-аккаунта, передав боту код авторизации (authorization code/grant).
            По коду авторизации бот получит от сервера YouTube токен доступа (access_token),
            по которому бот сможет отправлять запросы к YouTube API пока не истечет срок
            действия токена. По истечению срока, мы будет автоматически обновлять токен,
            то есть заменять его на новый действующий.
            """
            get_authenticated_service(user_id)

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

def add_filter(bot, update, args):
    pass


if __name__ == "__main__":
    # В отдельных потоках запускаем чеккер БД и граббер ВК.

    # ??? user_id для записи в таблицу posts БД будет получен только
    # после вызова юзером команды /start. Как запускать поток с
    # граббером только ПОСЛЕ вызова /start? .
    start_new_thread(vk_grabber, ())
    start_new_thread(start_checker, (bot,))

    updater = Updater(bot_token)

    updater.dispatcher.add_handler(CommandHandler("help", bot_help))
    updater.dispatcher.add_handler(CommandHandler("add", bot_add_network))
    updater.dispatcher.add_handler(CommandHandler("del", bot_del_network))
    updater.dispatcher.add_handler(CommandHandler("start", bot_start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, choice_handling))

    updater.start_polling()
    updater.idle()


"""
- Проверить запись значения networks в БД в choise_handling()
– 
"""