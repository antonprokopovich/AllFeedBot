"""
Граббер постов для каждой соц. сети будет получать название, содержание,
дату каждого нового поста, и добавлять их с соответствующим id в
строку таблицы 'Posts' нашей базы данных.
"""
import requests

vk_token = "a56dcc9cfab85e55830115734f36b6f56686bc685658a9dceba0c3d677423bd702b73b61fc240b78ee404"
vk_url = "https://api.vk.com/method/newsfeed.get?filters=post,photo&v=4.0&access_token={}".format(vk_token)


def vk_grabber():
    feed = requests.get(vk_url)
    feed_json = feed.json()

    posts = feed_json['response']['items']
    print(posts[0])

    
vk_grabber()

