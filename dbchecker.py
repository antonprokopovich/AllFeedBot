# 1. Берем из таблицы users данные о подписках, данные даты последнего
# поста для каждой подписки.
# 2. Для каждого пользователя, для каждой подписки проверяем новые посты.
# 3. Если есть новые, то пересылаем посты в канал. Сохраняем таймстэмпы последнего
# поста для каждой сети.
import traceback
import sqlite3
import json
import time

connection = sqlite3.connect('bot_db.db', check_same_thread=False)
cursor = connection.cursor()

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
def start_checker(bot): # принимает аргумент bot
        # Список всех пользователей.
        while True:
            cursor.execute('select * from users')
            user_list = cursor.fetchall()
            print(user_list)
            for user_row in user_list:
                #print(user_row)
                user_id = user_row[1]
                networks_dict = json.loads(user_row[2])
                channels_dict = json.loads(user_row[3])
                channel_name = user_row[4]
                print(channel_name)
                # Список добавленных соц-сетей и временных меток.
                subs_and_timestamps_networks = [
                (network, value['last_checked']) for network, value in networks_dict.items() if value['subscribed'] == True
                ]
                """
                # Список добавленных телеграм-каналов и временных меток.
                subs_and_timestamps_channels = [(channel, value['last_checked']) for channel, value in channels_dict.items()]
                # Объединяем соц-сети и телеграм-каналы (с метками last_checked) в единый список подписок.
                subs_and_timestamps = subs_and_timestamps_networks + subs_and_timestamps_channels
                """
                for sub, last_checked in subs_and_timestamps_networks:
                    #print(sub, last_checked)
                    # Список новых постов из соц. сети.
                    cursor.execute(
                        'select * from posts where user_id = ? and network = ? and timestamp > ? order by timestamp asc', 
                        [user_id, sub, last_checked]
                        )
                    posts = cursor.fetchall()
                    #print("number of new posts: ", len(posts))

                    if posts != []:
                        # Отправляем ссылку на каждый пост в канал.
                        for post in posts:
                            post_link = post[2]
                            post_body =post[1]
                            #print(post_body)

                            if post_link != None:
                                bot.send_message(channel_name, post_link)
                            else:
                                try:
                                    bot.send_message(channel_name, post_body)
                                except BaseException as e:
                                    continue
                        # Обновляем занчение last_cheked в ячейке networks.
                        last_post_timestamp = posts[-1][3]

                        """
                        if sub[0] == '@':
                            channels_dict[sub]['last_checked'] = last_post_timestamp
                            channels_dict_updated_json = json.dumps(channels_dict)
                            cursor.execute(
                                'update users set channels = ? where user_id = ?',
                                [channels_dict_updated_json, user_id]
                            )
                        """
                        networks_dict[sub]['last_checked'] = last_post_timestamp
                        networks_dict_updated_json = json.dumps(networks_dict)
                        cursor.execute(
                            'update users set networks = ? where user_id = ?',
                            [networks_dict_updated_json, user_id]
                        )
                        connection.commit()
            time.sleep(10*60)

"""
if __name__ == '__main__':
    while True:
        start_checker()
        time.sleep(30*60)
"""