# -*- coding: utf-8 -*-
from _thread import start_new_thread
import traceback
import json
import time

import sqlite3

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from telegram import User, ReplyKeyboardMarkup, Bot

from vk_grabber import vk_grabber
from youtube_grabber import youtube_grabber
from tg_grabber import telegram_grabber
# Из модуля проверки БД на наличие новых постов импортируем
# основную функцию.
from dbchecker import start_checker
from youtube_grabber import get_authenticated_service
from tg_grabber import join_channel

auth_host = "agrbot.info:8889"
bot_token = "781241991:AAF8n_sfMKiyNlXJ329-D2nRdrTwOURS6GE"
tbot = Bot(bot_token)

connection = sqlite3.connect('bot_db.db', check_same_thread=False, timeout=10)
cursor = connection.cursor()

# Телеграм-id пользователя будет инициализирован при первом обращении
# к боту, когда отправляется команда /start.
#user_id = None

# Позже добавим названия других сетей в список.
all_networks = ["VK", "YouTube"]


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
    автоматически при отправке. 
    """
    # При начале работы с ботом автоматически вызывается команда /start
    # и пользователю присвается user_id, под которым он заносится в БД.
    user_id = update.message.chat.id
    print(tbot.name)

    # Имя или юзернейм пользователя для приветствия.
    fname = update.message.from_user.first_name
    if not fname:
        fname = update.message.from_user.username

    channel_name = "@{}{}".format(user_id, fname)

    msg = "Приветствую, {}!".format(fname)
    msg += "\nСоздайте Телеграм-канал с названием {}," \
    "и добавте данного бота ({}) в администраторы канала.".format(channel_name, tbot.name)
    msg += "\n\nДля получения дальнейшей справки воспользуйтесь командой /help"

    update.message.reply_text(msg)
    # При старте работы с ботом заносим id юзера и название канала в БД.
    # Если пользователь повторно воспользовался командой /start,
    # и его данные уже есть в таблице - не меняем их.
    # (IGNORE или REPLACE ?)
    cursor.execute('INSERT or IGNORE INTO users (user_id, channel_name) VALUES (?, ?)', [user_id, channel_name])
    connection.commit()

@quiet_exec   
def bot_help(bot, update):
    """
    Хэндлер команды /help, которая дает справку о командах бота
    """
    commands = [
    "/help – получить справку.",
    "/add – добавить социальную сеть.",
    "/del – удалить социальную сеть.",
    "/add_channel @имя_канала – добавить Телеграм-канал",
    "/del_channel @имя_канала – удалить Телеграм-канал"
    ]
    update.message.reply_text("\n".join(commands))


def bot_add_channel(bot, update, args):
    """
    Хэндлер команды /add_channel и ее аргумента, которая добавляет в
    список рассылок телеграм-канал указанный в качестве аргумента.
    """
    channel_name = ''.join(args)
    if channel_name[0] != '@':
        msg = "Название канала должно начинаться с символа '@'."
        msg += "\nПопробуйте еще раз."
    else:
        try:
            join_channel(channel_name)
            msg = "Канал {} добавлен в вашу рассылку.".format(channel_name)
        except ValueError:
            msg = "Канал с таким названием не существует."

    update.message.reply_text(msg)
    #cursor.execute('update ')

def bot_del_channel(bot, update, args):
    pass



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

    user_id = update.message.chat.id
    # Выбираем из таблицы users БД данных запись соответствующую
    # текущему пользователю.
    cursor.execute(
        'select networks from users where user_id = ?', [json.dumps(user_id)]
    )
    # В формате json сохраняем данные из ячейки networks
    db_networks_json = cursor.fetchone()[0]
    # Конвертируем json в python-словарь
    user_networks_dict = json.loads(db_networks_json) 
    # Создаем список из соц. сетей, которые пользователь ранее добавил в рассылку.
    user_networks_list = [
        key for key, values in user_networks_dict.items() if values['subscribed'] == True
    ]
    #print('user_networks_list = {}'.format(user_networks_list))

    # Списки user_networks_list и networks_to_add являются обратными друг
    # дгуру: добавляя элемент в один из них, мы убираем его из дургого,
    # и наоборот.
    networks_to_add = [
    network for network in all_networks if network not in user_networks_list
    ]
    #print("networks_to_add = {}".format(networks_to_add))
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
        # ??? (Блок повторяется с предыдущим хэндлером. Вынести вне функций, сделав global user_id?)
    user_id = update.message.chat.id
    cursor.execute(
        'select networks from users where user_id = ?', [json.dumps(user_id)]
    )
    db_networks_json = cursor.fetchone()[0]
    user_networks_dict = json.loads(db_networks_json) 
    user_networks_list = [
        key for key, values in user_networks_dict.items() if values['subscribed'] == True
    ]

    if user_networks_list == []:
        msg = "Список рассылок пуст."
        markup = None
    else:
        reply_keyboard = [user_networks_list]
        msg = "Выберите сеть для удаления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)

@quiet_exec
def choice_handling(bot, update):
    """Хэндлер срабатывающий после того, как пользователь выбрал сеть
    для добавления/удаления, и обновляющий список рассылок networks в БД.
    """
    global adding

    user_id = update.message.chat.id
    chosen_network = update.message.text.lower()

    if adding:
        # Обновляем информацию о подписках пользователя в БД.
        cursor.execute(
            'select networks from users where user_id = ?',[user_id]
        )
        db_networks_json = cursor.fetchone()[0]
        user_networks_dict = json.loads(db_networks_json)
        # Добавляем сеть
        user_networks_dict[chosen_network] = {'subscribed': True, 'last_checked': int(time.time())}
        cursor.execute(
            'update users set networks = ? where user_id = ?',
            [json.dumps(user_networks_dict), user_id]
        )
        connection.commit()

        msg = "Сеть {} добавлена в вашу рассылку.".format(chosen_network[0].upper()+chosen_network[1:])

        if chosen_network == 'youtube':
            """
            Если добавлена сеть YouTube, то получаем права по OAuth.
            """
            auth_link = "http://{}/auth/youtube/?userid={}".format(auth_host, user_id)
            msg += "\nДля авторизации приложения перейдите по ссылке: {}".format(auth_link)

        msg += "\n\nДля добавления других сетей, повторно воспользуйтесь командой /add"

        adding = False
        update.message.reply_text(msg)

    else:
        # Обновляем информацию о подписках пользователя в БД.
        cursor.execute(
            'select networks from users where user_id = ?', [user_id]
        )
        db_networks_json = cursor.fetchone()[0]
        user_networks_dict = json.loads(db_networks_json)
        user_networks_dict[chosen_network] = {'subscribed': False, 'last_checked': int(time.time())}
        cursor.execute(
            'update users set networks = ? where user_id = ?',
            [json.dumps(user_networks_dict), user_id]
        )
        connection.commit()

        msg = "Сеть {} удалена из вашей рассылки".format(chosen_network[0].upper()+chosen_network[1:])
        msg += "\nДля удаления других сетей, повторно воспользуйтесь командой /del"
        update.message.reply_text(msg)

def add_filter(bot, update, args):
    pass


if __name__ == "__main__":
    # В отдельных потоках запускаем чеккер БД и граббер ВК.
    #start_new_thread(vk_grabber, ())
    #start_new_thread(youtube_grabber, ())

    start_new_thread(start_checker, (tbot,))

    updater = Updater(bot_token)

    updater.dispatcher.add_handler(CommandHandler("help", bot_help))
    updater.dispatcher.add_handler(CommandHandler("add_channel", bot_add_channel, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("del_channel", bot_del_channel, pass_args=True))
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


