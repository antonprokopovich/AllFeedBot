# 1. Берем из таблицы users данные о подписках, данные даты последнего
# поста для каждой подписки.
# 2. Для каждого пользователя, для каждой подписки проверяем новые посты.
# 3. Если есть новые, то пересылаем посты в канал. Сохраняем таймстэмпы последнего
# поста для каждой сети.
import sqlite3
import json

connection = sqlite3.connect('bot_db.db', check_same_thread=False)
cursor = connection.cursor()

def start_checker(bot):
    cursor.execute('select * from users')
    for user_row in cursor:
        # Строка json-формата из колонки networks таблицы users.
        networks_json = user_row[2]
        networks_dict = json.loads(networks_json)
        # Список сетей, которые добавил пользователь.
        subs = [
        network for network, value in networks_dict.items() if value['subscribed'] == True
        ]
        # Список временных меток последних отправленных постов для
        # каждой сети из предыдущего списка.
        subs_last_checked = [
        networks_dict[network]['last_checked'] for network in subs
        ]
        channel_name = user_row[3]

        for sub, last_checked in zip(subs, subs_last_checked):
            cursor.execute('select * from posts where network = ? and timestamp > ? order by timestamp asc', [sub, last_checked])
            for post_row in cursor:
                post_link = post_row[2]
                bot.send_message(channel_name, post_link)

