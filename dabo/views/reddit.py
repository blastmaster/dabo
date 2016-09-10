from dabo import app
from flask import request, redirect, url_for, render_template

import os
import sys
import json
import webbrowser

import praw
from newspaper import Article


def user_agent():

    base = 'test script 0.1 bu /u/'
    return ''.join([base, app.config['REDDIT_USERNAME']])

# TODO get rid of globals
reddit = praw.Reddit(user_agent=user_agent())
reddit.set_oauth_app_info(client_id=app.config['REDDIT_API_CLIENT_ID'],
                            client_secret=app.config['REDDIT_API_CLIENT_SECRET'],
                            redirect_uri=app.config['REDDIT_API_REDIRECT_URL'])


@app.route('/reddit')
def reddit_upvotes():

    articles = get_upvoted_articles()
    app.logger.debug('Rendering redditreads site')
    return render_template('redditreads.html', articles=articles)


@app.route('/reddit_callback')
def authorize():

    app.logger.debug('in reddit authorize callback')
    state = request.args.get('state', '')
    code = request.args.get('code', '')
    info = reddit.get_access_information(code)
    save_access_credentials(info)
    app.logger.debug('redirect to {}'.format(url_for('reddit_upvotes')))
    redirect(url_for('reddit_upvotes'))


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


def save_access_credentials(access_info, filename='access.json'):
    ''' writes access_token, refresh_token and scope to disk '''

    with open(filename, 'w+') as f:
        json.dump(access_info, f, default=json_set_to_list_hook)


def load_access_credentials(filename='access.json'):
    ''' Loads access_token, refresh_token and scope from disk
        Returns a python dict which should be accepted by set_access_information. '''

    if not os.path.isfile(filename):
        app.logger.debug('cannot find file: {}'.format(filename))
        return

    with open(filename) as f:
        j = json.load(f, object_hook=json_list_to_set_hook)
        return j


def _dump_submission(subm):
    ''' print title and url of a submission '''

    print('Title: {0}\nURL: {1}\n'.format(subm.title, subm.url))


def dump_upvoted(reddit):

    if not reddit.is_oauth_session():
        print("ERROR NO OAUTH SESSION", file=sys.stderr)

    me = reddit.get_me()
    for upvoted in me.get_upvoted():
        _dump_submission(upvoted)


def get_upvoted(reddit):

    if not reddit.is_oauth_session():
        print("ERROR NO OAUTH SESSION", file=sys.stderr)
        return

    upvoted = []
    me = reddit.get_me()
    for article in me.get_upvoted():
        upvoted.append(extract_article(article.url))
    return upvoted


def try_with_oAuth(r, access_code=None, scope='history'):

    auth_url = r.get_authorize_url('uniqueKey', scope, True)
    if not access_code:
        try:
            browser = webbrowser.get(app.config['BROWSER'])
        except Exception as e:
            print("{0} {1}".format(e, e.message), file=sys.stderr)
            # using default browser
            browser = webbrowser.get()
            pass

        browser.open_new_tab(auth_url)
    else:
        access_information = r.get_access_information(access_code)
        return access_information


def login():

    access_info = load_access_credentials()
    if not access_info:
        new_access_info = try_with_oAuth(reddit, scope=['history', 'identity'])
        reddit.set_access_credentials(scope=new_access_info['scope'],
                                      access_token=new_access_info['access_token'],
                                      refresh_token=new_access_info['refresh_token'])
    else:
        app.logger.debug('try to refresh...')
        new_acc_info = reddit.refresh_access_information(access_info['refresh_token'])
        save_access_credentials(new_acc_info)


def get_upvoted_articles():

    login()
    articles = get_upvoted(reddit)
    return articles

def extract_article(url):

    article = Article(url)
    article.download()
    article.parse()
    return {'title': article.title,
            'img': article.top_image,
            'publish_date': article.publish_date,
            'story_url': url,
            'text': article.text}
