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
– ? Как прописать в боте (tbot.py) команду/хэндлер для добавления каналов?
Предлагать вводить название канала в качестве аргумента команды?
– ? Создавать отдельную таблицу в БД для подписок на телеграм-каналы юзеров?
- ? Добавлять отдельный хэндлер для просмотра списка подписок на каналы,
чтобы юзер мог посмотреть на какие он уже подписан, и не добавлял/удалял
их повторно?
_ ? Клиент из telethon может сразу пересылать сообщения из каналов в канал,
тогда можно не сохранять сообщения в БД. Но тогда они будут идти отдельным
потоком от других соц. сетей и потоки не будут никак синхронизированны, а
сообщения двух потоков не будут отсортированны между друг другом.
Стоит использовать эту опцию?
–? Так же клиент может отправлять сообщения используя объект класса Message
телеграма. Значит если использовать ORM то можно сохранять считаные
клиентом объекты класса Message в базу, и потом воссоздавать их из базы
для перессылки юзеру?
""" 
import sqlite3
import json

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
# Название канала, ИЗ которого клиент будет пересылать посты (тестовый константный)
channel = '@science'
#my_channel = '@feed_channel'

# Создаем клиента, от лица которого можно действовать как пользователь телеграма
client = TelegramClient('session_name', api_id, api_hash)
client.connect()
# Если клиент не авторизован, авторизуем один раз по номеру телефона
if not client.is_user_authorized():
    client.send_code_request(phone_number)
    me = client.sign_in(phone_number, input('Enter code: '))
#client.send_message('self', 'Hello World from Telethon!')

# Клиентом можно вступать в канал или покидать его
#client(JoinChannelRequest(channel))
#client(LeaveChannelRequest(channel))
def join_channel(channel_name: str):
    client(JoinChannelRequest(channel_name))


def telegram_grabber():
    # Составляем список пользователей подписанных хотя бы на один канал.
    user_infos = [
        (user_id, json.loads(channels)) for user_id, channels in cursor.execute(
            'select user_id, channels from users where channels is not null and channels != "{}"'
        )
    ]
    for user_id, channels_dict in user_infos:
    # Названия каналов и соответствующие им метки last_checked
    # (в них будет id последнего сообщения канала).
        channel_names_and_timestamps = [
            (item[0], item[1]['last_checked']) for item in channels_dict.items()
        ]

        for channel_name, last_checked  in channel_names_and_timestamps:
            # Считываем клиентом все новые сообщения из канала.
            message_objects = client.iter_messages(channel_name, min_id=last_checked)
            for msg in message_objects:
                msg_id = msg.id
                msg_body = msg.message
                # Дату конвертим из UTC в unix
                msg_timestamp = int((msg.date.timestamp()))

                cursor.execute(
                    'inser into posts values (NULL, ?, NULL, ?, ?)', [msg_body, msg_timestamp, channel_name, user_id]
                )

client.disconnect()


