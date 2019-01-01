# -*- coding: utf-8 -*-
from _thread import start_new_thread
import traceback
import json
import time
import sqlite3
<<<<<<< HEAD
 
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, PreCheckoutQueryHandler
from telegram import User, ReplyKeyboardMarkup, Bot, LabeledPrice
 
=======

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, PreCheckoutQueryHandler
from telegram import User, ReplyKeyboardMarkup, Bot, LabeledPrice

>>>>>>> 91bc959a90fbaf01eb9f96a82192c64fd1224d39
from dbchecker import start_checker
 
auth_host = "agrbot.info:8889"
bot_token = "738165589:AAFxndvtTXmcZcXaSaP85V2S49ExfZKWCoY"
tbot = Bot(bot_token)
 
connection = sqlite3.connect('bot_db.db', check_same_thread=False, timeout=10)
cursor = connection.cursor()
 
all_networks = ["VK", "YouTube"]

# Флаг для перехода в режим удаления
# или добавления соц. сетей, чтобы хэндлер choice_handling(),
# обрабатывающий сообщение с название соц. сети, определял
# удалять или добавлять его в соответствии с текущем режимом.
adding = False

# Флаг перехода в режим оплаты премиум-подписки,
# чтобы хэндлер choice_hangling() считал название
# типа выбранной подписки и отправил форму для оплаты
paying = False
 
 
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
    #print(tbot.name)
    networks_dict = {'vk':{'subscribed': False, 'last_checked': int(time.time())}, 'youtube': {'subscribed': False, 'last_checked': int(time.time())}}
 
    # Имя или юзернейм пользователя для приветствия.
    fname = update.message.from_user.first_name
    username = update.message.from_user.username
    if not fname:
        fname = username
 
    channel_name = "@{}{}".format(user_id, fname)
 
    msg = "Приветствую, {}!".format(fname)
    msg += "\nСоздайте приватный Телеграм-канал с названием {}, " \
    "и добавьте данного бота ({}) в администраторы канала.".format(channel_name, tbot.name)
    msg += "\n\nДля получения дальнейшей справки воспользуйтесь командой /help"
 
    update.message.reply_text(msg)
    # При старте работы с ботом заносим id юзера и название канала в БД.
    # Если пользователь повторно воспользовался командой /start,
    # и его данные уже есть в таблице - не меняем их.
    # (IGNORE или REPLACE ?)
    cursor.execute(
        'insert or replace into users (user_id, networks, channel_name, username) VALUES (?, ?, ?, ?)',
        [user_id, json.dumps(networks_dict), channel_name, username]
    )
    connection.commit()
 
@quiet_exec  
def bot_help(bot, update):
    """
    Хэндлер команды /help, которая дает справку о командах бота
    """
    commands = [
    "/help – получить справку.\n",
    "/add – добавить социальную сеть.",
    "/del – удалить социальную сеть.",
    "/add_channel @имя_канала – добавить Телеграм-канал.",
    "/premium – снять ограничение на количество каналов."
    ]
    update.message.reply_text("\n".join(commands))
 
@quiet_exec
def bot_add_channel(bot, update, args):
    """
    Хэндлер команды /add_channel и ее аргумента, которая добавляет в
    список рассылок телеграм-канал указанный в качестве аргумента.
    """
    user_id = update.message.chat.id
 
    # Получаем из БД список каналов на которые юзер уже подписан
    cursor.execute(
        'select channels from users where user_id = ?', [json.dumps(user_id)]
        )
    channels_dict = json.loads(cursor.fetchone()[0])
    channels_list =[channel for channel in channels_dict.keys()]

    if args is None:
        msg = "Вы не указали имя_канала."
    else:
        channel_name = ''.join(args)
     
        if channel_name[0] != '@':
            msg = "Название канала должно начинаться с символа '@'."
            msg += "\nПопробуйте еще раз."
        elif channel_name in channels_list:
            msg = "Вы уже добавляли данный канал."
        else:
            msg = "Канал {} добавлен в вашу рассылку.".format(channel_name)
 
    update.message.reply_text(msg)
 
    # Заносим новый канал в БД
    channels_dict[channel_name] = {'last_checked': int(time.time())}
    cursor.execute('update users set channels = ? where user_id = ?', [json.dumps(channels_dict), user_id])
    connection.commit()
<<<<<<< HEAD
 
 
=======


# Флаг, который будет использоваться для перехода в режим удаления
# или добавления соц. сетей, чтобы хэндлер choice_handling(),
# обрабатывающий сообщение с название соц. сети, определял
# удалять или добавлять его в соответствии текущем режимом.
adding = False
>>>>>>> 91bc959a90fbaf01eb9f96a82192c64fd1224d39
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
    networks_json = cursor.fetchone()[0]
    # Конвертируем json в python-словарь
    user_networks_dict = json.loads(networks_json)
    # Создаем список из соц. сетей, которые пользователь ранее добавил в рассылку.
    user_networks_list = [
        key for key, values in user_networks_dict.items() if values['subscribed'] == True
    ]
    #print('user_networks_list = {}'.format(user_networks_list))
 
    # Списки user_networks_list и networks_to_add являются обратными друг
    # дгуру: добавляя элемент в один из них, мы убираем его из дургого,
    # и наоборот.
    networks_to_add = [
        network for network in all_networks if network.lower() not in user_networks_list
    ]
    #print("networks_to_add = {}".format(networks_to_add))
    #print(networks_to_add == [])
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
    """Хэндлер брабатывает команду /del и предоставляющий
    пользователю варианты доступных для добавления социальных сетей."""
    global adding
    adding = False
        # ??? (Блок повторяется с предыдущим хэндлером. Вынести вне функций, сделав global user_id?)
    user_id = update.message.chat.id
    cursor.execute(
        'select networks from users where user_id = ?', [json.dumps(user_id)]
    )
    networks_json = cursor.fetchone()[0]
    user_networks_dict = json.loads(networks_json)
    user_networks_list = [
        key for key, values in user_networks_dict.items() if values['subscribed'] == True
    ]
 
    if user_networks_list == []:
        msg = "Список рассылок пуст."
        markup = None
    else:
        # Для reply_keyboard берем "прописные" названия из списка all_networks.
        reply_keyboard = [
            [network for network in all_networks if network.lower() in user_networks_list]
        ]
        msg = "Выберите сеть для удаления:\n"
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(msg, reply_markup=markup)
 
@quiet_exec
def choice_handling(bot, update):
    """Хэндлер срабатывающий после того, как пользователь выбрал сеть
    для добавления/удаления или план безлимитной подписки.
    """
    global adding
    global paying
 
    user_id = update.message.chat.id
    chosen_network_uppercase = update.message.text
    chosen_network = chosen_network_uppercase.lower()
 
    # Если добавляем сеть
    if adding:
        cursor.execute(
            'select networks from users where user_id = ?',[user_id]
        )
        networks_json = cursor.fetchone()[0]
        user_networks_dict = json.loads(networks_json)
        # Добавляем сеть
        user_networks_dict[chosen_network] = {'subscribed': True, 'last_checked': int(time.time())}
        cursor.execute(
            'update users set networks = ? where user_id = ?',
            [json.dumps(user_networks_dict), user_id]
        )
        connection.commit()
 
        msg = "Сеть {} добавлена в список рассылок.".format(chosen_network_uppercase)
 
        if chosen_network == 'youtube':
            auth_link = "http://{}/auth/youtube/?userid={}".format(auth_host, user_id)
        else:
            auth_link = "http://{}/auth/vk/?userid={}".format(auth_host, user_id)
        msg += "\nДля авторизации приложения перейдите по ссылке: {}".format(auth_link)
 
        msg += "\n\nДля добавления других сетей, повторно воспользуйтесь командой /add"
 
        adding = False
        update.message.reply_text(msg)
 
    # Если удаляем сеть
    elif not adding and not paying:
        cursor.execute(
            'select networks from users where user_id = ?', [user_id]
        )
        networks_json = cursor.fetchone()[0]
        user_networks_dict = json.loads(networks_json)
        user_networks_dict[chosen_network] = {'subscribed': False, 'last_checked': int(time.time())}
        cursor.execute(
            'update users set networks = ? where user_id = ?',
            [json.dumps(user_networks_dict), user_id]
        )
        connection.commit()
 
        msg = "Сеть {} удалена из вашей рассылки.".format(chosen_network_uppercase)
        msg += "\nДля удаления других сетей, повторно воспользуйтесь командой /del"
        update.message.reply_text(msg)

<<<<<<< HEAD
    # Если оформляем платную подписку
    else:
        chosen_plan = update.message.text
        # TO DO: указывать дату начала и окончания подписки.
        if chosen_plan == "Месяц":
            title = "Премиум-подписка на месяц."
            price = 99
        elif chosen_plan == "Год":
            title = "Премиум-подписка на год."
            price = 499
        else:
            title = "Безлимитная премиум-подписка."
            price = 5999

        chat_id = update.message.chat.id
        description = "Прозволяет добавлять неограниченное число каналов."
        payload = "Custom-payload"
     
        provider_token = "381764678:TEST:7948"
        start_parameter = 'sub-payment'
     
        currency = "RUB"
        # Цены в целых значениях минимальных единиц валюты (копейки).
        prices = [
            LabeledPrice("Подписка на месяц.", price * 100),
        ]
     
        bot.sendInvoice(chat_id, title, description,
                        payload, provider_token, start_parameter,
                        currency, prices)
        paying = False

@quiet_exec
def bot_payment(bot, update):
    """Хэндлер запроса на оплату премиум-подписки.
    Предлагает выбор из доступных тарифов."""
    global paying
    paying = True

    msg = "Выберите тарифный план подписки:"
    reply_keyboard = [["Месяц\n99.00 RUB", "Год\n499.00 RUB", "Безлимит\n5999.00 RUB"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
=======
def bot_payment(bot, update, args):
    """Хэндлер запроса на оплату полной подписки.
    Формирует сообщение-счет и отправляет юзеру."""
    chat_id = update.message.chat.id
    title = "Full subscription"
    description = "Full subscription allows user to add unlimited amount of channels."
    payload = "Custom-payload"

    provider_token = "PROVIDER_TOKEN"
    start_parameter = 'sub-payment'

    currency = "RUR"
    price = 299 # Цена в рублях
    # Цена в целых значениях минимальных единиц валюты (копейки)
    prices = [LabeledPrice("Full subscription", price*100)]

    bot.sendInvoice(chat_id, title, description,
                    payload, provider_token, start_parameter,
                    currency, prices)

def precheckout_callback(bot, update, args):
    """Хэндлер проверяет корректность данных
    перед осуществлением оплаты"""
    query = update.pre_checkout_query
    if query.invoice_payload != "Custom-payload":
        # Ответ на ошибку при оплате
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                      error_message="Что-то пошло не так...")
    else:
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)

def successful_payment(bot, update, args):
    update.message.reply_text("Оплата прошла успешно!")

def add_filter(bot, update, args):
    pass

if __name__ == "__main__":
>>>>>>> 91bc959a90fbaf01eb9f96a82192c64fd1224d39

    update.message.reply_text(msg, reply_markup=markup)
    
 
def precheckout_callback(bot, update):
    """Хэндлер проверяет корректность данных
    перед осуществлением оплаты"""
    query = update.pre_checkout_query
    if query.invoice_payload != "Custom-payload":
        # Ответ на ошибку при оплате
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                      error_message="Что-то пошло не так...")
    else:
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
 
def successful_payment(bot, update):
    update.message.reply_text("Оплата прошла успешно!")
 
def add_filter(bot, update, args):
    pass
 
if __name__ == "__main__":
 
    start_new_thread(start_checker, (tbot,))
 
    updater = Updater(bot_token)
<<<<<<< HEAD
 
=======

>>>>>>> 91bc959a90fbaf01eb9f96a82192c64fd1224d39
    updater.dispatcher.add_handler(CommandHandler("start", bot_start))
    updater.dispatcher.add_handler(CommandHandler("help", bot_help))
    updater.dispatcher.add_handler(CommandHandler("add_channel", bot_add_channel, pass_args=True))
    updater.dispatcher.add_handler(CommandHandler("add", bot_add_network))
    updater.dispatcher.add_handler(CommandHandler("del", bot_del_network))
    updater.dispatcher.add_handler((CommandHandler("premium", bot_payment)))
    updater.dispatcher.add_handler((PreCheckoutQueryHandler(precheckout_callback)))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, choice_handling))
<<<<<<< HEAD
 
 
=======


>>>>>>> 91bc959a90fbaf01eb9f96a82192c64fd1224d39
    updater.start_polling()
    updater.idle()

"""

"""
