#!/usr/bin/env python

# TODO: move out all non-flask code to a separate file / library

import logging
import json
import requests
import zipfile
import io

from flask import Flask
from flask import Response
from flask import request
import flask_cors
import ee

import config

# if __name__ == '__main__':
#    import config
#else:
#    from . import config


app = Flask(__name__)
# Initialize the EE API.
# Use our App Engine service account's credentials.
EE_CREDENTIALS = ee.ServiceAccountCredentials(config.EE_ACCOUNT, config.EE_PRIVATE_KEY_FILE)
ee.Initialize(EE_CREDENTIALS)

# HydroBASINS level 5
basins = ee.FeatureCollection('ft:1IHRHUiWkgPXOzwNweeM89CzPYSfokjLlz7_0OTQl')

# HydroSHEDS rivers, 15s
rivers = ee.FeatureCollection('users/gena/HydroEngine/riv_15s_lev05')

# HydroLAKES
lakes = ee.FeatureCollection('users/gena/HydroLAKES_polys_v10')

# graph index
index = ee.FeatureCollection("users/gena/HydroEngine/hybas_lev05_v1c_index")

monthly_water = ee.ImageCollection("JRC/GSW1_0/MonthlyHistory")

# bathymetry
# TODO: merge all bathymetric data sets (GEBCO, EMODnet, Vaklodingen, JetSki, NOAA LiDAR, ...)
# TODO: add an argument in get_raster_profile(): bathymetric data set as an
# TODO: add an argument in get_raster_profile(): datetime
# TODO: add an argument in get_raster_profile(): reducer (max, min, mean, ...)
bathymetry = ee.ImageCollection('users/gena/vaklodingen').filterDate('2010-01-01', '2019-01-01').mean()

def get_upstream_catchments(basin_source) -> ee.FeatureCollection:
    hybas_id = ee.Number(basin_source.get('HYBAS_ID'))
    upstream_ids = index.filter(ee.Filter.eq('hybas_id', hybas_id)).aggregate_array('parent_from')
    upstream_basins = basins.filter(ee.Filter.inList('HYBAS_ID', upstream_ids)).merge(
        ee.FeatureCollection([basin_source]))

    return upstream_basins

def number_to_string(i):
    return ee.Number(i).format('%d')

def reduceImageProfile(image, line, reducer, scale):
    length = line.length()
    distances = ee.List.sequence(0, length, scale)
    lines = line.cutLines(distances).geometries();

    def generate_line_segment(l):
        l = ee.List(l)
        geom = ee.Geometry(l.get(0))
        distance = ee.Geometry(l.get(1))

        geom = ee.Algorithms.GeometryConstructors.LineString(geom.coordinates())

        return ee.Feature(geom, {'distance': distance})

    lines = lines.zip(distances).map(generate_line_segment)
    lines = ee.FeatureCollection(lines)

    # reduce image for every segment
    band_names = image.bandNames()

    return image.reduceRegions(lines, reducer.setOutputs(band_names), scale)

@app.route('/get_raster_profile', methods=['GET', 'POST'])
@flask_cors.cross_origin()
def api_get_raster_profile():
    polyline = ee.Geometry(request.json['polyline'])
    scale = float(request.json['scale'])

    reducer = ee.Reducer.mean()

    data = reduceImageProfile(bathymetry, polyline, reducer, scale).getInfo()

    # fill response
    resp = Response(json.dumps(data), status=200, mimetype='application/json')

    return resp

@app.route('/get_catchments', methods=['GET', 'POST'])
def api_get_catchments():
    bounds = ee.Geometry(request.json['bounds'])

    selection = basins.filterBounds(bounds)

    # for every selection, get and merge upstream
    upstream_catchments = ee.FeatureCollection(selection.map(get_upstream_catchments)).flatten().distinct('HYBAS_ID')

    # dissolve output
    # TODO: dissolve output

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
    upstream_catchment_ids = ee.List(upstream_catchments.aggregate_array('HYBAS_ID')).map(number_to_string)

    # query rivers
    upstream_rivers = rivers \
        .filter(ee.Filter.inList('HYBAS_ID', upstream_catchment_ids)) \
        .select(['ARCID', 'UP_CELLS', 'HYBAS_ID'])

    # filter upstream branches
    if 'filter_upstream_gt' in request.json:
        filter_upstream = int(request.json['filter_upstream_gt'])
        print('Filtering upstream branches, limiting by {0} number of cells'.format(filter_upstream))
        upstream_rivers = upstream_rivers.filter(ee.Filter.gte('UP_CELLS', filter_upstream))

    # create response
    url = upstream_rivers.getDownloadURL('json')

    data = {'url': url}

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

@app.route('/get_lakes', methods=['GET', 'POST'])
def api_get_lakes():
    bounds = ee.Geometry(request.json['bounds'])
    id_only = bool(request.json['id_only'])

    selection = basins.filterBounds(bounds)

    # for every selection, get and merge upstream catchments
    upstream_catchments = ee.FeatureCollection(selection.map(get_upstream_catchments)).flatten().distinct('HYBAS_ID')

    region = upstream_catchments.geometry()

    # query lakes
    upstream_lakes = ee.FeatureCollection(lakes.filterBounds(region))

    if id_only:
      ids = upstream_lakes.aggregate_array('Hylak_id')

      return Response(json.dumps(ids.getInfo()), status=200, mimetype='application/json')

    # create response
    url = upstream_lakes.getDownloadURL('json')

    data = {'url': url}

    return Response(json.dumps(data), status=200, mimetype='application/json')

@app.route('/get_lake_by_id', methods=['GET', 'POST'])
def get_lake_by_id():
    lake_id = int(request.json['lake_id'])

    lake = ee.Feature(ee.FeatureCollection(lakes.filter(ee.Filter.eq('Hylak_id', lake_id))).first())

    return Response(json.dumps(lake.getInfo()), status=200, mimetype='application/json')

def get_lake_water_area(lake_id, scale):
    f = ee.Feature(lakes.filter(ee.Filter.eq('Hylak_id', lake_id)).first())

    def get_monthly_water_area(i):
        # get water mask
        water = i.clip(f).eq(2)

        s = scale
        if not scale:
            # estimate scale from reservoir surface area, currently
            coords = ee.List(f.geometry().bounds().transform('EPSG:3857', 30).coordinates().get(0))
            ll = ee.List(coords.get(0))
            ur = ee.List(coords.get(2))
            width = ee.Number(ll.get(0)).subtract(ur.get(0)).abs()
            height = ee.Number(ll.get(1)).subtract(ur.get(1)).abs()
            size = width.max(height)

            MAX_PIXEL_COUNT = 1000

            s = size.divide(MAX_PIXEL_COUNT).max(30)

            print('Automatically estimated scale is: ' + str(s))

        # compute water area
        water_area = water.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), f.geometry(), s).values().get(0)

        return ee.Feature(None, {'time': i.date().millis(), 'water_area': water_area })

    area = monthly_water.map(get_monthly_water_area)

    area_values = area.aggregate_array('water_area')
    area_times = area.aggregate_array('time')

    return { 'time': area_times.getInfo(), 'water_area': area_values.getInfo() }

@app.route('/get_lake_time_series', methods=['GET', 'POST'])
def api_get_lake_time_series():
    lake_id = int(request.json['lake_id'])
    variable = str(request.json['variable'])

    scale = None
    if 'scale' in request.json:
        scale = int(request.json['scale'])

    if variable == 'water_area':
        ts = get_lake_water_area(lake_id, scale)

        return Response(json.dumps(ts), status=200, mimetype='application/json')

    return Response('Unknown variable', status=404, mimetype='application/json')

@app.route('/get_raster', methods=['GET', 'POST'])
def api_get_raster():
    variable = request.json['variable']
    bounds = ee.Geometry(request.json['bounds'])
    cell_size = float(request.json['cell_size'])
    crs = request.json['crs']

    selection = basins.filterBounds(bounds)

    # for every selection, get and merge upstream
    upstream_catchments = ee.FeatureCollection(selection.map(get_upstream_catchments)).flatten().distinct('HYBAS_ID')

    # region = upstream_catchments.geometry(cell_size).dissolve(cell_size)

    # skip dissolve - much faster version
    region = upstream_catchments.geometry().bounds()

    raster_assets = {
        'dem': 'USGS/SRTMGL1_003',
        'hand': 'users/gena/global-hand/hand-100',
        'FirstZoneCapacity': 'users/gena/HydroEngine/static/FirstZoneCapacity',
        'FirstZoneKsatVer': 'users/gena/HydroEngine/static/FirstZoneKsatVer',
        'FirstZoneMinCapacity': 'users/gena/HydroEngine/static/FirstZoneMinCapacity',
        'InfiltCapSoil': 'users/gena/HydroEngine/static/InfiltCapSoil',
        'M': 'users/gena/HydroEngine/static/M',
        'PathFrac': 'users/gena/HydroEngine/static/PathFrac',
        'WaterFrac': 'users/gena/HydroEngine/static/WaterFrac',
        'thetaS': 'users/gena/HydroEngine/static/thetaS',
        'soil_type': 'users/gena/HydroEngine/static/wflow_soil',
        'landuse': 'users/gena/HydroEngine/static/wflow_landuse',
        'LAI01': 'users/gena/HydroEngine/static/LAI/LAI00000-001',
        'LAI02': 'users/gena/HydroEngine/static/LAI/LAI00000-002',
        'LAI03': 'users/gena/HydroEngine/static/LAI/LAI00000-003',
        'LAI04': 'users/gena/HydroEngine/static/LAI/LAI00000-004',
        'LAI05': 'users/gena/HydroEngine/static/LAI/LAI00000-005',
        'LAI06': 'users/gena/HydroEngine/static/LAI/LAI00000-006',
        'LAI07': 'users/gena/HydroEngine/static/LAI/LAI00000-007',
        'LAI08': 'users/gena/HydroEngine/static/LAI/LAI00000-008',
        'LAI09': 'users/gena/HydroEngine/static/LAI/LAI00000-009',
        'LAI10': 'users/gena/HydroEngine/static/LAI/LAI00000-010',
        'LAI11': 'users/gena/HydroEngine/static/LAI/LAI00000-011',
        'LAI12': 'users/gena/HydroEngine/static/LAI/LAI00000-012'
    }

    if variable == 'hand':
        image = ee.ImageCollection(raster_assets[variable]).mosaic()
    else:
        image = ee.Image(raster_assets[variable])

    image = image.clip(region)

    # create response
    url = image.getDownloadURL({
        'name': 'variable',
        'format': 'tif',
        'crs': crs,
        'scale': cell_size,
        'region': json.dumps(region.bounds(cell_size).getInfo())
    })

    data = {'url': url}
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/')
def root():
    return 'Welcome to Hydro Earth Engine. Currently, only RESTful API is supported. Visit <a href="http://github.com/deltares/hydro-engine">http://github.com/deltares/hydro-engine</a> for more information ...'


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
