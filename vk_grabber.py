"""
Граббер постов для каждой соц. сети будет получать название, содержание,
дату каждого нового поста, и добавлять их с соответствующим id в
строку таблицы 'Posts' нашей базы данных.
"""
import requests
import sqlite3
import time

connection = sqlite3.connect('bot_db.db', check_same_thread=False)
cur = connection.cursor()

# Дата последнего поста из VK занесенного в базу данных. Далее по ней будем
# определять до какого поста идут новые, а после какого старые (уже 
# занесенные в базу данных).
cur.execute("SELECT timestamp FROM posts WHERE network = 'vk' ORDER BY timestamp DESC LIMIT 1")
last_timestamp_vk = cur.fetchone()[0]
#print(last_timestamp)
#---------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------------
vk_token = "a56dcc9cfab85e55830115734f36b6f56686bc685658a9dceba0c3d677423bd702b73b61fc240b78ee404"
# Использоую last_timestamp_vk и vk_token формируем ссылку для
# http-запроса к VK API для получения данных всех последних постов.
vk_url = ("https://api.vk.com/method/newsfeed.get?start_time={}&filters=post,photo&v=4.0&access_token={}"
        .format(last_timestamp_vk, vk_token))

def vk_grabber():
    while True:
        network_name = 'vk'
        r = requests.get(vk_url)
        data = r.json()
        print(data)
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

                cur.execute("insert into posts values (NULL, ?, ?, ?, ?, ?)", [text, vk_link, timestamp, network_name])
            connection.commit()
    # Парсим новые посты из новостной ленты ВК каждую минуту.     
    time.sleep(30*60)    


   
