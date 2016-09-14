from dabo import app
from flask import request, redirect, url_for, render_template
from flask.views import View

import os
import sys
import json
import webbrowser

import praw
from newspaper import Article

''' utility functions '''

def get_user_agent():

    base = 'test script 0.1 bu /u/'
    return ''.join([base, app.config['REDDIT_USERNAME']])


def json_set_to_list_hook(obj):
    ''' convert a set to a list to make it json serializable '''

    if isinstance(obj, set):
        return list(obj)
    return obj


def json_list_to_set_hook(obj):
    ''' replaces set with list to make json decode return equivalent to json encode input '''

    for k, v in obj.items():
        if isinstance(v, list):
            obj.update({k: set(v)})

    return obj


def extract_article(url):

    article = Article(url)
    article.download()
    article.parse()
    return {'title': article.title,
            'img': article.top_image,
            'publish_date': article.publish_date,
            'story_url': url,
            'text': article.text}


class RedditAgent:
    ''' Reddit Agent: Handles authentication and requests to the reddit API. '''

    def __init__(self, user_agent=None):

        self.reddit = praw.Reddit(user_agent=get_user_agent())
        self.reddit.set_oauth_app_info(client_id=app.config['REDDIT_API_CLIENT_ID'],
                client_secret=app.config['REDDIT_API_CLIENT_SECRET'],
                redirect_uri=app.config['REDDIT_API_REDIRECT_URL'])
        self.access_code = None

    @property
    def is_oauth(self):
        return self.reddit.is_oauth_session()

    def save_access_credentials(self, access_info=None, filename='access.json'):
        ''' writes access_token, refresh_token and scope to disk '''

        if not access_info:
            access_info = self.access_code

        with open(filename, 'w+') as f:
            json.dump(access_info, f, default=json_set_to_list_hook)

    def load_access_credentials(self, filename='access.json'):
        ''' Loads access_token, refresh_token and scope from disk
            Returns a python dict which should be accepted by set_access_information. '''

        if not os.path.isfile(filename):
            app.logger.debug('cannot find file: {}'.format(filename))
            return

        with open(filename) as f:
            self.access_code = json.load(f, object_hook=json_list_to_set_hook)
            return self.access_code

    def get_upvoted(self):

        if not self.is_oauth:
            print("ERROR NO OAUTH SESSION", file=sys.stderr)
            return

        upvoted = []
        me = self.reddit.get_me()
        for article in me.get_upvoted():
            upvoted.append(extract_article(article.url))
        return upvoted

    def request_auth(self, scope='history'):

        auth_url = self.reddit.get_authorize_url('uniqueKey', scope, True)
        try:
            browser = webbrowser.get(app.config['BROWSER'])
        except Exception as e:
            print("{0} {1}".format(e, e.message), file=sys.stderr)
            # using default browser
            browser = webbrowser.get()
            pass

        browser.open_new_tab(auth_url)

    def login(self):

        if self.is_oauth:
            app.logger.debug('already in oauth session')
            return

        access_info = self.load_access_credentials()
        if not access_info:
            self.request_auth(scope=['history', 'identity'])
            return

        app.logger.debug('try to refresh...')
        self.access_code = self.reddit.refresh_access_information(access_info['refresh_token'])
        self.save_access_credentials()


class RedditView(View):

    def __init__(self, reddit_agent=None):
        self.agent = reddit_agent

    def dispatch_request(self):

        self.agent.login()
        articles = self.agent.get_upvoted()
        app.logger.debug('Rendering redditreads site')
        return render_template('redditreads.html', articles=articles, views=app.config['PLUGINS'])


class RedditAuthView(View):

    def __init__(self, reddit_agent=None):
        self.agent = reddit_agent

    def dispatch_request(self):

        app.logger.debug('in reddit authorize callback')
        state = request.args.get('state', '')
        code = request.args.get('code', '')
        info = self.agent.reddit.get_access_information(code)
        self.agent.save_access_credentials(info)
        app.logger.debug('redirect to {}'.format(url_for('reddit_upvotes')))
        return redirect(url_for('reddit_upvotes'))


agent = RedditAgent()
app.add_url_rule('/reddit', view_func=RedditView.as_view('reddit_upvotes', reddit_agent=agent))
app.add_url_rule('/reddit_callback', view_func=RedditAuthView.as_view('reddit_callback', reddit_agent=agent))
