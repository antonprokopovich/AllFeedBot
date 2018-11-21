# 1. Берем из таблицы users данные о подписках, данные даты последнего
# поста для каждой подписки.
# 2. Для каждого пользователя, для каждой подписки проверяем новые посты.
# 3. Если есть новые, то пересылаем посты в канал. Сохраняем таймстэмпы последнего
# поста для каждой сети.
import sqlite3
import json
import time

connection = sqlite3.connect('bot_db.db', check_same_thread=False)
cursor = connection.cursor()

def start_checker(bot): # принимает аргумент bot
        # Список всех пользователей.
        cursor.execute('select * from users')
        for user_row in cursor:
            user_id = user_row[1]
            networks_json = user_row[2]
            networks_dict = json.loads(networks_json)
            # Список соц. сетей, которые добавил пользователь.
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
                #print(sub, last_checked)
                # Список новых постов из соц. сети.
                cursor.execute(
                    'select * from posts where user_id = ? and network = ? and timestamp > ? order by timestamp asc', [user_id, sub, last_checked]
                    )
                posts = cursor.fetchall()
                #print(len(posts))
                if posts != []:
                    # Отправляем ссылку на каждый пост в канал.
                    for post in posts:
                        post_link = post[2]
                        if post_link != None:
                            bot.send_message(channel_name, post_link)
                        else:
                            post_body = post[1]
                            bot.send_message(channel_name, post_body)
                    # Обновляем занчение last_cheked в ячейке networks.
                    last_post_timestamp = posts[-1][3]
                    networks_dict[sub]['last_checked'] = last_post_timestamp
                    networks_dict_json_updated = json.dumps(networks_dict)
                    cursor.execute('update users set networks = ? where user_id = ?', (networks_dict_json_updated, user_id))
                    connection.commit()

if __name__ == '__main__':
    while True:
        start_checker()
        time.sleep(30*60)