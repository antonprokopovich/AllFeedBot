import json
import os

import sqlite3
import tornado.ioloop
import tornado.web
import torndsession
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery


CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

success_url = "http://agrbot.info:8889/success/"

connection = sqlite3.connect('bot_db.db')
cursor = connection.cursor()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("")

class SuccessHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Авторизация успешно пройдена.")


class OAuthCallbackYoutubeHandler(tornado.web.RequestHandler):
    def get(self):
        state = self.get_cookie('state')
        user_id = self.get_cookie('userid')
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
        flow.redirect_uri = "http://{}/oauth2callback/youtube/".format(self.request.host)
        
        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = self.request.uri
        flow.fetch_token(authorization_response=authorization_response)
        
        # Store the credentials in the session.
        # ACTION ITEM for developers:
        #     Store user's access and refresh tokens in your data store if
        #     incorporating this code into your real app.
        creds = flow.credentials
        creds_dict = {
            'refresh_token': creds.refresh_token,
            'access_token': creds.token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret
        }
        #self.write("USER_ID:" + user_id)
        #self.write("CREDS="+json.dumps(creds_dict, indent=4))
        self.redirect(success_url)
        # сохраняем credentials в БД.
        cursor.execute(
            'insert or replace into oauth_creds values (NULL, ?, ?, ?, ?, ?, ?, ?)',
            list(creds_dict.values()) + ['youtube', user_id]
        )
        connection.commit()


class AuthYoutubeHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_argument('userid', '')#.decode()
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
        flow.redirect_uri = "http://{}/oauth2callback/youtube/".format(self.request.host)
        authorization_url, state = flow.authorization_url(
        # This parameter enables offline access which gives your application
        # both an access and refresh token.
        access_type='offline',
        # This parameter enables incremental auth.
        include_granted_scopes='true')

        self.set_cookie('state', state)
        self.set_cookie('userid', user_id)
        self.redirect(authorization_url)

class OAuthCallbackVKHandler(tornado.web.RequestHandler):
    def get(self):
        network = "vk"
        user_id = self.get_cookie('userid')
        access_token = self.get_argument('access_token', '')
        """
        Если спаршенный токен пуст, значит вк редиректнул и в url была решетка - заменяем
        решетку на вопрос и редиректимся на себя.
        """
        if access_token == '':
            self.write(
                '<html><head></head><body><script>'
                'window.location.href = window.location.href.replace("#", "?");'
                '</script></body></html>'
            )
            return
        
        cursor.execute(
            "insert or replace into oauth_creds (access_token, network, user_id) values (?, ?)",
            [access_token, network, user_id]
        )
        connection.commit()

class AuthVKHandler(tornado.web.RequestHandler):
    def get(self):
        user_id = self.get_argument('userid', '')
        # Параметры запроса для формирования ссылки для авторизации
        client_id = 6761766 # id приложения FeedBot
        scope = "".join(['wall', 'friends', 'offline']) # параметр offline дает вечныей токен
        redirect_uri = "http://{}/oauth2callback/vk/".format(self.request.host)
        # Ссылка авторизации VK на которую будем редиректить ВСЕХ юзеров
        #authorization_url = "https://oauth.vk.com/authorize?redirect_uri=http://oauth.vk.com/blank.html&response_type=token&client_id=6750460&scope=wall,friends,offline&display=page"
        authorization_url = "https://oauth.vk.com/authorize?redirect_uri={}&response_type=token&client_id={}&scope={}&display=page".format(redirect_uri, client_id, scope)
        self.set_cookie('userid', user_id)
        self.redirect(authorization_url)



def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/success/", SuccessHandler),
        (r"/auth/youtube/", AuthYoutubeHandler),
        (r"/oauth2callback/youtube/", OAuthCallbackYoutubeHandler),
        (r"/auth/vk/", AuthVKHandler),
        (r"/oauth2callback/vk/", OAuthCallbackVKHandler)
    ])

if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app = make_app()
    app.listen(8889)
    tornado.ioloop.IOLoop.current().start()