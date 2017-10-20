import logging
import json
import requests
import zipfile
import io

from flask import Flask
from flask import Response
from flask import request

import ee

if __name__ == '__main__':
    import config
else:
    from . import config


app = Flask(__name__)

# Initialize the EE API.
# Use our App Engine service account's credentials.
EE_CREDENTIALS = ee.ServiceAccountCredentials(config.EE_ACCOUNT, config.EE_PRIVATE_KEY_FILE)
ee.Initialize(EE_CREDENTIALS)

# HydroBASINS level 5
basins = ee.FeatureCollection('ft:1IHRHUiWkgPXOzwNweeM89CzPYSfokjLlz7_0OTQl')

# HydroSHEDS rivers, 15s
rivers = ee.FeatureCollection('users/gena/HydroEngine/riv_15s_lev05')

# graph index
index = ee.FeatureCollection("users/gena/HydroEngine/hybas_lev05_v1c_index")


def get_upstream_catchments(basin_source) -> ee.FeatureCollection:
    hybas_id = ee.Number(basin_source.get('HYBAS_ID'))
    upstream_ids = index.filter(ee.Filter.eq('hybas_id', hybas_id)).aggregate_array('parent_from')
    upstream_basins = basins.filter(ee.Filter.inList('HYBAS_ID', upstream_ids)).merge(
        ee.FeatureCollection([basin_source]))

    return upstream_basins


@app.route('/get_catchments', methods=['GET', 'POST'])
def api_get_catchments():
    print(request)

    bounds = ee.Geometry(request.json['bounds'])

    selection = basins.filterBounds(bounds)

    # for every selection, get and merge upstream
    upstream_catchments = ee.FeatureCollection(selection.map(get_upstream_catchments)).flatten().distinct('HYBAS_ID')

    # dissolve output
    # TODO

    # get GeoJSON
    data = upstream_catchments.getInfo()  # TODO: use ZIP to prevent 5000 feature limit

    # fill response
    resp = Response(json.dumps(data), status=200, mimetype='application/json')

    return resp


@app.route('/get_rivers', methods=['GET', 'POST'])
def api_get_rivers():
    bounds = ee.Geometry(request.json['bounds'])

    selection = basins.filterBounds(bounds)

    # for every selection, get and merge upstream catchments
    upstream_catchments = ee.FeatureCollection(selection.map(get_upstream_catchments)).flatten().distinct('HYBAS_ID')

    # get ids
    upstream_catchment_ids = ee.List(upstream_catchments.aggregate_array('HYBAS_ID'))

    # query rivers
    upstream_rivers = rivers \
        .filter(ee.Filter.inList('hybas_id', upstream_catchment_ids)) \
        .select(['arcid', 'up_cells', 'hybas_id'])

    # filter upstream branches
    if 'filter_upstream_gt' in request.json:
        filter_upstream = int(request.json['filter_upstream_gt'])
        print('Filtering upstream branches, limiting by {0} number of cells'.format(filter_upstream))
        upstream_rivers = upstream_rivers.filter(ee.Filter.gte('up_cells', filter_upstream))

    # create response
    url = upstream_rivers.getDownloadURL('JSON')

    data = {'catchment_rivers_url': url}
    return Response(json.dumps(data), status=200, mimetype='application/json')

    # data = upstream_rivers.getInfo()  # TODO: use ZIP to prevent 5000 features limit
    # return Response(json.dumps(data), status=200, mimetype='application/octet-stream')

    # zip = zipfile.ZipFile(io.BytesIO(response.content))
    #
    # data = {
    #     'catchment_rivers': zip.namelist()
    # }
    #
    # resp = Response(json.dumps(data), status=200, mimetype='application/json')
    #
    # return resp


@app.route('/')
def root():
    return 'Welcome to Hydro Earth Engine. Currently, only RESTful API is supported. Work in progress ...'


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
