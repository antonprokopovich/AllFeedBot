"""
Граббер постов для каждой соц. сети будет получать название, содержание,
дату каждого нового поста, и добавлять их с соответствующим id в
строку таблицы 'Posts' нашей базы данных.
"""
import requests

import sqlite3

conn = sqlite3.connect('bot_db.db')
cur = conn.cursor()

# Дату последнего поста занесенного в базу данных. Далее по ней будем
# определять до какого поста идут новые, а после какого старые (уже 
# занесенные в базу данных).
last_post_date = cur.execute('select date from posts order by date desc limit 1')

vk_token = "a56dcc9cfab85e55830115734f36b6f56686bc685658a9dceba0c3d677423bd702b73b61fc240b78ee404"
vk_url = "https://api.vk.com/method/newsfeed.get?start_time={}filters=post,photo&v=4.0&access_token={}".format(vk_token)

def vk_grabber():
    r = requests.get(vk_url)
    data = r.json()

    posts = data['response']['items']
    for post in posts:
        date = post.get('date', 0)
        text = post.get('text', '')
        source_id = post.get('source_id', 0)
        post_id = post.get('post_id', 0)
        vk_link = "https://vk.com/feed?w=wall{}_{}".format(source_id, post_id)

        #print("TEXT: {}\nVK_LINK: {}\n------------------------------".format(text, vk_link))
 
    #cur.execute("insert into posts values (id, date, body, link")


youtube_token = "AIzaSyDu4VUNm9MQFigi8dgNZdb2nBIEvooYe-g"
youtube_url = ""

vk_grabber()
   
