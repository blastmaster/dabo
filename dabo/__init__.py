#! /usr/bin/env python3

from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.config.from_envvar('DABO_SETTINGS', silent=True)

import pprint
app.logger.debug('configs: {}'.format(pprint.pprint(app.config)))

''' load view plugins '''
import dabo.views

@app.route('/')
def index():
    # TODO:
    # Load available plugins in a ring-list.
    # response = render_template('layout.html', views=app.config['PLUGINS'])
    # TODO:
    # If no plugins there provide some index page.
    return redirect(url_for(app.config['PLUGINS'][0]['endpoint']))


@app.template_filter('plugin_name')
def strip_plugin_name(name):
    if name.startswith('.'):
        return name[1:]
    return name
