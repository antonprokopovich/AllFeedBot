# Sample Python code for user authorization

import os

import google.oauth2.credentials

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

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

def get_authenticated_service():    
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()
    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)


def my_subscriptions_ids_list(service, **kwargs):
"""
Метод выполняет get запрос к api методу list() ресурса subscriptions(),
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
Метод возвращает id плейлиста загруженных видео для каждого канала. 
"""
    results = service.channels().list(
        **kwargs
        ).execute()
    uploads_pl_id = results['items']['contentDetails']["relatedPlaylists"]["uploads"]
    return uploads_pl_id

def uploads_playlist_videos_ids_and_dates(service, **kwargs):
"""
Метод возвращает id (и таймкод, чтобы сортировать позже) каждого видео
загруженного на канал.
"""
    results = service.playlistItems().list(
        **kwargs
        ).execute()
    videos_ids = [item["contentDetails"]["videoId"] for item in results['items']]
    videos_dates_iso = [item["contentDetails"]["videoPublishedAt"] for item in results['items']]
    videos_ids_and_dates = [(video_id, video_date) for video_id, video_date in zip(videos_ids, videos_dates_iso)]
    # Сортируем список кортежей (id, время) по времени.
    videos_ids_and_dates = sorted(videos_ids_and_dates, key=lambda x: x[1])
    return videos_ids_and_dates


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification. When
    # running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()


    # Получаем список id каналов, на которые подписан пользователь.
    sub_ids_list = my_subscriptions_ids_list(service,
            part='snippet',
            mine=True,
            maxResults=50)

    # Получаем список из id плейлистов загрузок каждого канала.
    uploads_pl_ids_list = []
    for sub_id in sub_ids_list:
        uploads_pl_id = channel_uploads_playlist_id(service,
                part='contentDetails',
                id=sub_id,
                maxResults=50)
    uploads_pl_ids_list.append(uploads_pl_id)

    # Получаем список из списков (id и таймкодов) для каждого видео для
    # каждого канала (то есть все видео со всех каналов, на которые подписан
    # пользователь).
    subs_videos_ids_and_dates = []
    for uploads_pl_id in uploads_pl_ids_list:
        videos_ids_and_dates = uploads_playlist_videos_ids_and_dates(service,
            part='contentDetails',
            playlistId=uploads_pl_id,
            maxResults=50)
            subs_videos_ids_and_dates.append(videos_ids_and_dates)
    # Сортируем список видео по их таймкодам.        
    subs_videos_ids_and_dates = sorted(subs_videos_ids_and_dates, key=lambda x: x[1])
    
    # Для каждого видео формируем ссылку на него и его таймкод для
    # последующего сохранения в БД.
    for id_and_date in subs_videos_ids_and_dates:
        youtube_link = "https://www.youtube.com/watch?v={}".format(id_and_date[0])
        timestamp_iso = id_and_date[1]





""" 



















