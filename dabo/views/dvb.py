from dabo import app
from flask import render_template
from flask.views import View

import time
import requests


class DepatureSchedule(View):

    def dispatch_request(self):

        depature_schedules = {}
        for station, schedule in dvb_depature_schedule(app.config['DVB_STATIONS_TIMES']):
            depature_schedules.update({station: schedule})

        app.logger.debug('Rendering publictransport site')
        return render_template('publictransport.html', schedules=depature_schedules, views=app.config['PLUGINS'])


def dvb_depature_schedule(stations):
    ''' Takes an list of tuples containing the station and the duration to that
    station. Builds the url with the appropriate parameters, make the request
    and yields a tuple containing the station name and the response data as
    json. '''

    ''' depature schedule url '''
    URL = "http://widgets.vvo-online.de/abfahrtsmonitor/Abfahrten.do"

    for station, tm in stations:
        params = {'ort': 'Dresden',
                  'hst': station,
                  'vz': tm,
                  'timestamp': int(time.time())}

        data = requests.get(URL, params=params)
        if data.ok:
           yield (station, data.json())
        else:
            print("get status code {}".format(data.status_code))


app.add_url_rule('/dvb', view_func=DepatureSchedule.as_view('dvb_depature'))
