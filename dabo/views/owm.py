from dabo import app
from flask import render_template
from flask.views import View

import os
import requests
import time
import json

import pprint

class WeatherView(View):
    ''' View class for openweathermap data. '''

    def dispatch_request(self):

        api_key = app.config['OWM_API_KEY']
        city_id = app.config['OWM_CITY_ID']
        cache_file = app.config['OWM_CACHE_FILE']

        weather_data = get_owm_weather(api_key, city_id, cache_file)
        app.logger.debug('Rendering weather site')
        pprint.pprint(weather_data)
        return render_template('weather.html', weather=weather_data, views=app.config['PLUGINS'])


def get_owm_weather(api_key, city_id, cache_file):

    myowm = Owm(cache_file, api_key)
    data = myowm.weather(city_id)
    return data

class DaboRequestError(Exception):
    pass


class Owm:

    def __init__(self, cache_file, api_key, units='metric'):
        self.cache_file = cache_file
        self.api_key = api_key
        self.params = {"units": units,
                       "APPID": self.api_key }

    def make_request(self, url, parameters):

        app.logger.debug('request openweathermap api')
        req = requests.get(url, params=parameters)
        if req.ok:
            data = req.json()
            self.cache_data(data)
            return data
        else:
            raise DaboRequestError('Error: got: {0} when try to GET {1}'.format(req, req.url))

    def weather(self, city_id):
        ''' Get the current weather data. '''

        data = None
        url = "http://api.openweathermap.org/data/2.5/weather"
        self.params.update({'id': city_id})
        if not self.cache_expired():
            data = self.cache_read()
        else:
            data = self.make_request(url, self.params)

        return data

    def cache_expired(self):
        ''' We store each response from OpenWeatherMaps in a json file.
            If such a file exists and has a modified timestamp older than 10 minutes
            the cached file expires. Then a new request to get fresh data would be
            made.

            Check if cache file is expired.

            Returns True if the cache file is expired or does not exist and false if
            cache is valid.
        '''
        if os.path.exists(self.cache_file):
            now = time.time()
            mtime = os.stat(self.cache_file).st_mtime
            exp_time = mtime + 600    # cache file expires 10 minutes after mtime
            if now < exp_time:
                return False

        return True


    def cache_read(self):
        ''' Read the cache file and load its content in a json object.
            The cache file will be read without any further checks.
            It is assumed it exists and is readable. '''

        app.logger.debug('read cache file')
        with open(self.cache_file, 'r') as cf:
            return json.load(cf)


    def cache_data(self, data):

        with open(self.cache_file, 'w+') as cf:
            json.dump(data, cf)


app.add_url_rule('/weather', view_func=WeatherView.as_view('weather'))
