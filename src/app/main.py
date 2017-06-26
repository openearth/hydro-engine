# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging
import json

from flask import Flask
from flask import Response
from flask import request

import ee

import config

app = Flask(__name__)

# Initialize the EE API.
# Use our App Engine service account's credentials.
EE_CREDENTIALS = ee.ServiceAccountCredentials(config.EE_ACCOUNT, config.EE_PRIVATE_KEY_FILE)

ee.Initialize(EE_CREDENTIALS)

basins = ee.FeatureCollection('ft:1IHRHUiWkgPXOzwNweeM89CzPYSfokjLlz7_0OTQl')

def traverse_up(basins_source):
    filter_next_up = ee.Filter.equals(leftField='NEXT_DOWN', rightField='HYBAS_ID')
    
    join = ee.Join.inner('primary', 'secondary').apply(basins, basins_source, filter_next_up)
  
    existing = basins_source.aggregate_array('HYBAS_ID')
    
    def get_parent(feature):
        return feature.get('primary')
  
    return join.map(get_parent)

@app.route('/get_catchment', methods = ['GET', 'POST'])
def api_get_catchment():
    bounds = ee.Geometry(request.json['bounds'])
    depth = int(request.json['depth'])

    current = basins.filterBounds(bounds)

    fc = current
    for i in range(depth):
        current = traverse_up(current)

        fc = fc.merge(current)

    
    results = fc.geometry().dissolve(100)
  
    data = {
        'catchmen_boundary': results.getInfo()
    }

    resp = Response(json.dumps(data), status=200, mimetype='application/json')

    return resp


@app.route('/')
def hello():
    return 'Welcom to Hydro Earth Engine. Currently, only RESTful API is supported. Work in progress ...'


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]

