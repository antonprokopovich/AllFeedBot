"""
- Создаем телеграм-клиента, который сможет подписываться на каналы,
отписываться, считывать новые сообщения в каналах, и добавлять их в БД
- Если юзер добавляет через бота (tbot.py) новый канал, то клиент 
подписывается на данный канал, если не был уже подписан для других юзеров, 
заносит в БД информацию о новой подписке юзера и текущее время в качестве
метки last_checked.
- Если все юзеры отписались от конкретного канала, клиент тоже
отписывается от него.(?)
– Раз в n минут клиент считывает сообщения в каждом канале,
на который подписан юзер, начиная с id (по тайкоду сложнее) последнего
сообщения (поста) занесенного в БД. Считанное сообщение разбирается
на содержимое (текст, медиафайлы и т.п.) и заносится в таблицу posts
БД.
– Данный процесс проводится для каждого пользователя. 

    ВОПРОСЫ:
- ? Добавлять отдельный хэндлер для просмотра списка подписок на каналы,
чтобы юзер мог посмотреть на какие он уже подписан, и не добавлял/удалял
их повторно?
–? Так же клиент может отправлять сообщения используя объект класса Message
телеграма. Значит если использовать ORM то можно сохранять считаные
клиентом объекты класса Message в базу, и потом воссоздавать их из базы
для перессылки юзеру?
""" 
import traceback
import sqlite3
import json
import time

from datetime import datetime
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.sync import TelegramClient
#from telethon.tl.custom import Message

connection = sqlite3.connect('bot_db.db')
cursor = connection.cursor()

# Данные для создания телеграм-клиента
api_id = 654585
api_hash = "85b15b1918e06814c3a052f4d6e44718"
phone_number = 89852549143


# Создаем клиента, от лица которого можно действовать как пользователь телеграма
client = TelegramClient('session_name', api_id, api_hash)
client.connect()
# Если клиент не авторизован, авторизуем один раз по номеру телефона
if not client.is_user_authorized():
    client.send_code_request(phone_number)
    me = client.sign_in(phone_number, input('Enter code: '))
#client.send_message('@n3tw0rk3r', 'Hello World from Telethon!')

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
def telegram_grabber():
    #client.connect()
    # Составляем список пользователей подписанных хотя бы на один канал.
    user_infos = [
        (username, json.loads(channels), channel_name) for username, channels, channel_name in cursor.execute(
            'select username, channels, channel_name from users where channels is not null and channels != "{}"'
        )
    ]
    #print(user_infos)
    for username, channels_dict, channel_name in user_infos:
    # Названия каналов и соответствующие им метки last_checked
    # (в них будет id последнего сообщения канала).

        channels_and_timestamps = [
            (item[0], item[1]['last_checked']) for item in channels_dict.items()
        ]
        #print(channels_and_timestamps)
        for channel, last_checked  in channels_and_timestamps:
            # Вступаем клиентом в канал
            #channel_entity = client.get_entity(channel)

            try:
                client(JoinChannelRequest(channel))
            except ValueError:
                continue
            # Считываем клиентом все новые сообщения из канала.
            # Возвращает объект класса 'telethon.sync._SyncGen'
            message_objects = client.iter_messages(channel, offset_date=last_checked, reverse=True)
            #print(type(next(message_objects)))
            # Пересылаем юзеру новые сообщения клиентом напрямую
            # (без сохранения в БД)
            msg_list = [m for m in message_objects]
            #print(type(msg_list[0]))
            if msg_list != []:
                for msg in message_objects:
                    #print(type(next(message_objects)))
                    msg.forward_to(channel_name)
                    #client.send_message(username, next(message_objects))
                    """
                    #msg_id = msg.id
                    #msg_body = msg.message
                    # Дату конвертим из UTC в unix
                    #msg_media = msg.
                    #msg_timestamp = int((msg.date.timestamp()))

                    #cursor.execute(
                    #    'insert into posts values (NULL, ?, NULL, ?, ?, ?)', [msg_body, msg_timestamp, channel, username])
                    #connection.commit()
                    """
                last_msg_timestamp = int(msg_list[-1].date.timestamp())
                channels_dict['last_checked'] = last_msg_timestamp
                cursor.execute('update users set channels = ? where username = ?', [json.dumps(channels_dict), username])
                connection.commit()
            return

if __name__=='__main__':

    while True:
        telegram_grabber()
        client.disconnect()
        time.sleep(10*60)

"""
- Как send_message работает через username, если последний может
повторятся для разных пользователей.
"""
