"""
- Создаем телеграм-клиента, который сможет подписываться на каналы,
отписываться, считывать новые сообщения в каналах, и добавлять их в БД
- Если юзер добавляет через бота (tbot.py) новый канал, то клиент 
подписывается на данный канал, если не был уже подписан для других юзеров, 
заносит в БД информацию о новой подписке юзера и текущее время в качестве
метки last_checked.
- Если все юзеры отписались от конкретного канала, клиент тоже
отписывается от него.
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

from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.sync import TelegramClient
from telethon.tl.custom import Message

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

# Вступаем клиентом в канал
client(JoinChannelRequest(channel))
"""
msg_ids =[]
msgs = []
for msg in client.iter_messages(channel, limit=5):
    msg_ids.append(msg.id)
    msgs.append(msg.message)


client.send_message('self', client.get_messages(channel)[0])

"""
print(client.get_messages(channel)[0].date)
print(type(client.get_messages(channel)[0].date))

def datetime_to_unix(time_iso):
    """
    Функция для перевода временного кода в формате datetime (формат
    используемый telegram'ом) в формат unix time (формат для нашей БД).
    """
    parsed_t = dp.parse(time_iso)
    unix_time = parsed_t.strftime('%s')
    return unix_time

def get_new_messages(channel, last_msg_id):
    message_objects = client.iter_messages(channel, min_id=last_msg_id)
    for msg in message_objects:
        msg_id = msg.id
        msg_body = msg.message
        msg_timestamp = int(iso_to(msg.date))

# In the same way, you can also leave such channel
#client(LeaveChannelRequest(channel))


client.disconnect()

