#! /usr/bin/env python3

from flask import Flask, render_template

app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.config.from_envvar('DABO_SETTINGS', silent=True)

import pprint
app.logger.debug('configs: {}'.format(pprint.pprint(app.config)))

# TODO: loading plugins
import dabo.views.dvb
import dabo.views.reddit


@app.route('/')
def index():
    # TODO:
    # load available plugins, plugins are managed in a ring-list
    # choose first plugin
    return render_template('layout.html')
