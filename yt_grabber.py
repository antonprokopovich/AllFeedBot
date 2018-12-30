# -*- coding: utf-8 -*-
import os
import json
import time

import sqlite3
import google.oauth2.credentials
import google.auth.transport

from dateutil import parser as dp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

connection = sqlite3.connect('bot_db.db', check_same_thread=False)
cursor = connection.cursor()

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

# Переменная, хранящая данные авторизации.
credentials = None


def safe_api_request(func):
    """
    Декоратор, который отлавливает exception'ы о просроченном access
    token'е и обновляет его
    """
    def wrapper(*args, **kw):
        try:
            # Вызываем функцию с ее аргументами
            return func(*args, **kw)
        except RefreshError:
            print('[YT_GRABBER] Credentials are expired, refreshing...')
            # Обвновляем access token и получаем новый объект
            # ресурса (новый service с обновленным токеном)
            user_id = args[1]

            creds = load_creds(user_id)
            args[0] = refresh_access_token(creds)
            # Еще раз вызываем функцию
            return func(*args, **kw)

    return wrapper


def refresh_access_token(creds):
    """
    Функция обновляет access token, используя текущий refresh token
    """
    creds.refresh(google.auth.transport.requests.Request())
    return build(API_SERVICE_NAME, API_VERSION, credentials = creds)


def save_creds(creds, user_id):
    """
    Сохраняем credentials в БД.
    """
    network = 'youtube'
    creds_dict = {
        'refresh_token': creds.refresh_token,
        'access_token': creds.token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret
    }
    """
    with open('creds.json', 'w') as f:
        f.write(json.dumps(creds_dict))
    """
    cursor.execute(
        'insert or replace into oauth_creds values (NULL, ?, ?, ?, ?, ?, ?, ?)',
        list(creds_dict.values())+[network, user_id]
    )
    connection.commit()


def load_creds(user_id):
    """
    Получаем сохраненные данные и создаем объект 
    google.oauth2.credentials.Credentials (https://bit.ly/2POf6e0).
    Если данных нет, то возвращаем None
    """
    try:
        # Из БД получаем credentials юзера:
        # [access_token, refresh_token, token_uri, client_id, client_secret]
        print('[YT_GRABBER] Trying to load creds from DB...')
        cursor.execute('select * from oauth_creds where user_id = ?', (user_id,))
        creds_list = cursor.fetchone()[1:]

        print('[YT_GRABBER] Credentials info for {}: {}'.format(user_id, creds_list))
        # Создаем объект google.oauth2.credentials.Credentials из списка
        creds = google.oauth2.credentials.Credentials(
            creds_list[0],
            refresh_token=creds_list[1],
            token_uri=creds_list[2],
            client_id=creds_list[3],
            client_secret=creds_list[4],
        )
        """
        with open('creds.json', 'r') as f:
            # Загружаем данные из файла и создаем словарь
            creds_dict = json.loads(f.read())
            # Создаем объект google.oauth2.credentials.Credentials из словаря
            creds = google.oauth2.credentials.Credentials(
                creds_dict['access_token'],
                refresh_token=creds_dict['refresh_token'],
                token_uri=creds_dict['token_uri'],
                client_id=creds_dict['client_id'],
                client_secret=creds_dict['client_secret'],
            )
        """
        # Если access_token в credentials просрочен, то обновляем его
        if creds.expired:
            refresh_access_token(creds)
        return creds
    except BaseException as e:
        print(e)
        return


def get_authenticated_service(user_id):
    """
    Получаем ресурс (для API запросов). Для этого используются oauth
    данные пользователя (credentials), получаемые функцией load_creds
    из БД по Телеграм-id пользователя, который передается аргументом
    функции (user_id).
    """
    #global credentials

    # Пытаемся получить сохраненные ранее credentials,
    # если не удается - создаем их и сохраняем
    credentials = load_creds(user_id)
    if credentials is None:
        return None
    """
        credentials = flow.run_local_server(self, host='localhost',
            port=8888,
            authorization_prompt_message=_DEFAULT_AUTH_PROMPT_MESSAGE,
            success_message=_DEFAULT_WEB_SUCCESS_MESSAGE,
            open_browser=True)
    """
    save_creds(credentials, user_id) # сохраняем в БД для будущих запусков

    # Возвращаем русурс И user_id, чтобы по нему можно было обновлять access_tocken
    # через декоратор safe_api_request (см. первую функцию).
    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)


def iso_to_unix(time_iso):
    """
    Функция для перевода даты в формате iso (формат
    используемый youtube'ом) в формат unix time (формат для нашей БД).
    """
    parsed_t = dp.parse(time_iso)
    unix_time = parsed_t.strftime('%s')
    return unix_time


@safe_api_request
def my_subscriptions(service, user_id,  **kwargs):
    """
    Функция выполняет get запрос к api методу list() ресурса subscriptions(),
    и берет из ответа id каналов, на которые подписан аутентифицированный
    пользователь.
    """
    results = service.subscriptions().list(
        **kwargs
    ).execute()
    subs_ids = [
        item['snippet']["resourceId"]['channelId'] for item in results['items']
    ]
    return subs_ids


@safe_api_request
def channel_uploads_playlist_id(service, user_id, **kwargs):
    """
    Функция возвращает id плейлиста загруженных видео для каждого канала. 
    """
    results = service.channels().list(
        **kwargs
        ).execute()

    uploads_pl_id = (
        results['items'][0]['contentDetails']["relatedPlaylists"]["uploads"]
    )
    return uploads_pl_id


@safe_api_request
def uploads_playlist_videos_ids_and_dates(service, user_id, **kwargs):
    """
    Функция возвращает *список кортежей*, состоящих из id и таймкода
    (чтобы сортировать позже) каждого видео загруженного на канал.
    """
    results = service.playlistItems().list(
        **kwargs
        ).execute()

    videos_ids = [
        item["contentDetails"]["videoId"] for item in results['items']
    ]
    videos_dates_iso = [
        item["contentDetails"]["videoPublishedAt"] for item in results['items']
    ]

    zipped_ids_dates = zip(videos_ids, videos_dates_iso)
    videos_ids_and_dates = [
        (video_id, video_date) for video_id, video_date in zipped_ids_dates
    ]
    # Сортируем список кортежей (id, время) по времени.
    videos_ids_and_dates = sorted(videos_ids_and_dates, key=lambda x: x[1])

    return videos_ids_and_dates


def yt_grabber():
    """
    """
    print('[YT_GRABBER] yt_grabber started...')
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Итерируем по всем пользователям, подписанным на
    # рассылку YouTube.
    users_data = [
        (user_id, json.loads(networks)) for user_id, networks in cursor.execute(
            "select user_id, networks from users"
        )
    ]
    # Если не подписан - пропускаем...
    for user_id, networks in users_data:
        if networks['youtube']['subscribed'] != True:
            print('[YT_GRABBER] Skipping {}...'.format(user_id))
            continue

        print('[YT_GRABBER] Getting creds for {}...'.format(user_id))
        service = get_authenticated_service(user_id)
        # Функция get_authenticated_service возвращает None, если юзер еще не
        # авторизовал бота, в этом случае - пропускаем юзера.
        if service is None:
            print('[YT_GRABBER] {} did not go through authorization yet. Skipping...'.format(user_id))
            continue
        # Временная метка последнего YouTube-видео занесенного в базу данных. Далее по
        # ней будем определять до какой записи идут новые, а после какой старые
        # (уже занесенные в базу данных) видео.
        last_checked = networks['youtube']['last_checked']

        # Получаем список id каналов, на которые подписан пользователь.
        sub_ids_list = my_subscriptions(service, user_id,
                part='snippet',
                mine=True,
                maxResults=50
            )

        # Получаем список из id плейлистов загрузок каждого канала.
        uploads_pl_ids_list = []
        for sub_id in sub_ids_list:
            uploads_pl_id = channel_uploads_playlist_id(service, user_id,
                part='contentDetails',
                id=sub_id,
                maxResults=50
            )
            uploads_pl_ids_list.append(uploads_pl_id)

        # Получаем *список из списков из кортежей* (id и таймкодов) для
        # последних n видео (n = maxResults) для каждого канала (то есть
        # видео со всех каналов, на которые подписан пользователь).
        subs_videos_ids_and_dates = []
        for uploads_pl_id in uploads_pl_ids_list:
            videos_ids_and_dates = uploads_playlist_videos_ids_and_dates(service, user_id,
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
        subs_videos_ids_and_dates = sorted(
            subs_videos_ids_and_dates, key=lambda x: x[1]
        )
        print("[YT_GRABBER] There are {} new videos for user {}...".format(len(subs_videos_ids_and_dates), user_id))

        # ПАРСИНГ
        # Для каждого видео каждого канала формируем ссылку на него и его
        # таймкод для последующего сохранения в БД.
        for id_and_date in subs_videos_ids_and_dates:
            video_id, date = id_and_date
            network_name = 'youtube'
            video_link = "https://www.youtube.com/watch?v={}".format(video_id)
            timestamp = int(iso_to_unix(date))
            if timestamp > last_checked:
                cursor.execute(
                    "insert into posts values (NULL, NULL, ?, ?, ?, ?)",
                    [video_link, timestamp, network_name, user_id]
                )
                print("[YT_GRABBER] New youtube post added to the database.")
                connection.commit()

#"""
if __name__ == '__main__':
    while True:
        yt_grabber()
        time.sleep(10*60)
#"""