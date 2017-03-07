from dabo import app
from flask import request, redirect, url_for, render_template
from flask.views import View

import os
import sys
import json

import praw
from newspaper import Article

''' dabo Reddit Plugin - renders preview of the users upvoted reddit articles.

    This plugin requires OAuth credentials for Reddit API script applications.
'''

# utility functions

def get_user_agent():

    base = 'test script 0.1 by /u/'
    return ''.join([base, app.config['REDDIT_USERNAME']])


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

        self.reddit = praw.Reddit(client_id=app.config['REDDIT_API_CLIENT_ID'],
                                  client_secret=app.config['REDDIT_API_CLIENT_SECRET'],
                                  password=app.config['REDDIT_PASSWORD'],
                                  user_agent=get_user_agent(),
                                  username=app.config['REDDIT_USERNAME'])
        # self.reddit.read_only = True    # set to read only mode
        self.access_code = None

    def get_upvoted(self):
        ''' Get upvoted articles.
            Returns a list conatins upvoted articles. 
        '''

        upvoted = []
        me = self.reddit.user.me()
        for article in me.upvoted():
            app.logger.debug('get article {}'.format(article))
            upvoted.append(extract_article(article.url))
        return upvoted


class RedditView(View):

    def __init__(self, reddit_agent=None):
        self.agent = reddit_agent

    def dispatch_request(self):

        app.logger.debug('start fetching reddit articles')
        articles = self.agent.get_upvoted()
        app.logger.debug('get {} articles'.format(len(articles)))
        app.logger.debug('Rendering redditreads site')
        return render_template('redditreads.html', articles=articles, views=app.config['PLUGINS'])


class RedditAuthView(View):

    def __init__(self, reddit_agent=None):
        self.agent = reddit_agent

    def dispatch_request(self):

        app.logger.debug('in reddit authorize callback')
        app.logger.debug('redirect to {}'.format(url_for('reddit_upvotes')))
        return redirect(url_for('reddit_upvotes'))


agent = RedditAgent()
app.add_url_rule('/reddit', view_func=RedditView.as_view('reddit_upvotes', reddit_agent=agent))
app.add_url_rule('/reddit_callback', view_func=RedditAuthView.as_view('reddit_callback', reddit_agent=agent))
