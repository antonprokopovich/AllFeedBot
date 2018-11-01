"""
Граббер постов для каждой соц. сети будет получать название, содержание,
дату каждого нового поста, и добавлять их с соответствующим id в
строку таблицы 'Posts' нашей базы данных.
"""
import requests

import sqlite3

conn = sqlite3.connect('bot_db.db')
cur = conn.cursor()

vk_token = "a56dcc9cfab85e55830115734f36b6f56686bc685658a9dceba0c3d677423bd702b73b61fc240b78ee404"
vk_url = "https://api.vk.com/method/newsfeed.get?filters=post,photo&v=4.0&access_token={}".format(vk_token)


def vk_grabber():
    last_post_date = ''
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
 
# cur.execute("insers into posts values (id, title, body")
