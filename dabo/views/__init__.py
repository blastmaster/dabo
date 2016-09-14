from importlib import import_module
from dabo import app

# TODO:
for plugin in app.config['PLUGINS']:
    print('try to load: {}'.format(plugin))
    mod = import_module(plugin['name'], 'dabo.views')
    print('imported ... {}'.format(mod.__name__))
