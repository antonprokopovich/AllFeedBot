"""
Граббер постов для каждой соц. сети будет получать название, содержание,
дату каждого нового поста, и добавлять их с соответствующим id в
строку таблицы 'Posts' нашей базы данных.
"""
import requests
import time
import json

import sqlite3

connection = sqlite3.connect('bot_db.db', check_same_thread=False)
cursor = connection.cursor()

def vk_grabber():
    # Формируем список id всех пользователей, подписанных на
    # рассылку VK.
    user_infos = [
        (user_id, json.loads(networks)) for user_id, networks in cursor.execute(
            'select user_id, networks from users'
            )
    ]
    # ПАРСИНГ:
    # Для каждого пользователя парсим ссылки на новые видео и сохраняем в БД.
    for user_id, user_networks in user_infos:
        if user_networks['vk']['subscribed'] != True:
            continue
        # Получаем временную метку last_checked
        cursor.execute('select networks from users where user_id = ?', [user_id])
        networks_dict = json.loads(cursor.fetchone()[0])
        last_timestamp = networks_dict['vk']['last_checked']
        # Получаем access_token
        cursor.execute('select access_token from oauth_creds where user_id = ?', [user_id])
        access_token = cursor.fetchone()[0]
        # Используем временую метку и токен для формирования запроса к api
        url = ("https://api.vk.com/method/newsfeed.get?start_time={}&filters=post,photo&v=4.0&access_token={}"
        .format(last_timestamp, access_token))
        r = requests.get(url)
        data = r.json()
        #print(data)
        posts = data['response']['items']
        # Парсим, если есть новые посты (список posts не пуст).
        if posts != []:
            for post in posts:
                timestamp = post.get('date', 0)
                text = post.get('text', '')
                source_id = post.get('source_id', 0)
                post_id = post.get('post_id', 0)
                vk_link = "https://vk.com/feed?w=wall{}_{}".format(source_id, post_id)
                #print("TEXT: {}\nVK_LINK: {}\n------------------------------".format(text, vk_link))
                cursor.execute("insert into posts values (NULL, ?, ?, ?, ?, ?)", [text, vk_link, timestamp, 'vk', user_id])
                connection.commit()
#"""
if __name__ == '__main__':
    while True:
        vk_grabber()
        time.sleep(10*60)
#"""
