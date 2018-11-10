# -*- coding: utf-8 -*-
import os
import json

import sqlite3
import google.oauth2.credentials

from dateutil import parser as dp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

connection = sqlite3.connect('bot_db.db')
cursor = connection.cursor()

# Дата последнего YouTube-видео занесенного в базу данных. Далее по
# ней будем определять до какого поста идут новые, а после какого старые
# (уже занесенные в базу данных).
cursor.execute(
    "SELECT timestamp FROM posts WHERE network = 'youtube' "
    "ORDER BY timestamp DESC LIMIT 1"
)
#print(cursor.fetchone())
last_timestamp_youtube = cursor.fetchone()[0]

# Переменная CLIENT_SECRETS_FILE хранит имя файла, который содержит
# информацию связанную с OAuth 2.0 для данного приложения, включая
# его client_id и client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# Данная область доступа OAuth 2.0 предоставляет полный доступ для
# чтения/записи к аутентифицированному аккаунту пользователя и требует
# чтобы запросы использовали SSL соединение.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def safe_api_request(func):
    """
    ...
    """
    def wrapper(*args, **kw):
        try:
            # Вызываем функцию с ее аргументами
            return func(*args, **kw)
        except RefreshError:
            service = args[0]
            credentials = service.credentials
            #credentials.refresh_token
    return wrapper

def save_tokens(creds):
    """
    Сохраняем refresh token в текстовый файл.
    """
    tokens = {
        'refresh_token': creds.refresh_token,
        'access_token': creds.access_token
    }
    with open('tokens.txt', 'w') as f:
        f.write(json.dumps(tokens))

def get_authenticated_service():
"""
"""    
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()

    save_tokens(credentials)
    service = build(API_SERVICE_NAME, API_VERSION, credentials = credentials)
    service.credentials = credentials
    return service

def iso_to_unix(time_iso):
    """
    Функция для перевода временного кода в формате iso (формат
    используемый youtube'ом) в формат unix time (формат для нашей БД).
    """
    parsed_t = dp.parse(time_iso)
    unix_time = parsed_t.strftime('%s')
    return unix_time

def my_subscriptions(service, **kwargs):
    """
    Функция выполняет get запрос к api методу list() ресурса subscriptions(),
    и берет из ответа id каналов, на которые подписан аутентифицированный
    пользователь.
    """
    results = service.subscriptions().list(
        **kwargs
    ).execute()
    subs_ids = [item['snippet']["resourceId"]['channelId'] for item in results['items']]
    #print('ID каналов на которые вы подписаны: {}'.format(", ".join(subs_ids)))
    return subs_ids


def channel_uploads_playlist_id(service, **kwargs):
    """
    Функция возвращает id плейлиста загруженных видео для каждого канала. 
    """
    results = service.channels().list(
        **kwargs
        ).execute()
    uploads_pl_id = results['items'][0]['contentDetails']["relatedPlaylists"]["uploads"]
    return uploads_pl_id

def uploads_playlist_videos_ids_and_dates(service, **kwargs):
    """
    Функция возвращает *список кортежей*, состоящих из id и таймкода
    (чтобы сортировать позже) каждого видео загруженного на канал.
    """
    results = service.playlistItems().list(
        **kwargs
        ).execute()
    videos_ids = [item["contentDetails"]["videoId"] for item in results['items']]
    videos_dates_iso = [item["contentDetails"]["videoPublishedAt"] for item in results['items']]

    zipped_ids_dates = zip(videos_ids, videos_dates_iso)
    videos_ids_and_dates = [
        (video_id, video_date) for video_id, video_date in zipped_ids_dates
    ]
    # Сортируем список кортежей (id, время) по времени.
    videos_ids_and_dates = sorted(videos_ids_and_dates, key=lambda x: x[1])

    return videos_ids_and_dates



def youtube_grabber():
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()


    # Получаем список id каналов, на которые подписан пользователь.
    sub_ids_list = my_subscriptions(
            service,
            part='snippet',
            mine=True,
            maxResults=50
        )

    # Получаем список из id плейлистов загрузок каждого канала.
    uploads_pl_ids_list = []
    for sub_id in sub_ids_list:
        uploads_pl_id = channel_uploads_playlist_id(
            service,
            part='contentDetails',
            id=sub_id,
            maxResults=50
        )
        uploads_pl_ids_list.append(uploads_pl_id)
    #print(uploads_pl_ids_list)

    # Получаем *список из списков из кортежей* (id и таймкодов) для
    # последних n видео (n = maxResults) для каждого канала (то есть
    # видео со всех каналов, на которые подписан пользователь).
    subs_videos_ids_and_dates = []
    for uploads_pl_id in uploads_pl_ids_list:
        videos_ids_and_dates = uploads_playlist_videos_ids_and_dates(
            service,
            part='contentDetails',
            playlistId=uploads_pl_id,
            maxResults=10
        )
        subs_videos_ids_and_dates.append(videos_ids_and_dates)
    # Из списка списков кортежей делаем просто список кортежей
    # (раскрываем список каждого канала), чтобы можно было отсортировать
    # по таймкоду все видео со всех каналов.
    subs_videos_ids_and_dates = [
        tup for channel_list in subs_videos_ids_and_dates 
                for tup in channel_list
    ]
    # Сортируем список видео по их таймкодам.        
    subs_videos_ids_and_dates = sorted(subs_videos_ids_and_dates, key=lambda x: x[1])
    #print(subs_videos_ids_and_dates)


#if __name__ == '__main__':
    
    # Формируем список id всех пользователей, подписанных на
    # рассылку YouTube.
    users_ids = [
        user_id[0] for user_id in cursor.execute(
        "SELECT user_id FROM users WHERE networks LIKE '%youtube%'")
    ]

    # Для каждого видео каждого канала формируем ссылку на него и его
    # таймкод для последующего сохранения в БД.
    for channel_list in subs_videos_ids_and_dates:
        video_id, date = channel_list
        # Переписать user_id
        user_id = user
        network_name = 'youtube'
        video_link = "https://www.youtube.com/watch?v={}".format(video_id)

        timestamp = int(iso_to_unix(date))
        if timestamp > last_timestamp_youtube:
            cursor.execute(
                "insert into posts values (NULL, NULL, ?, ?, ?, ?)",
                [video_link, timestamp, network_name, user_id]
            )
    connection.commit()

"""
- Добавить итерацию по пользователям, переменную user_id.

"""
#if __name__ == '__main__':

