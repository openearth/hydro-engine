#!/usr/bin/env python

# TODO: move out all non-flask code to a separate file / library

import logging
import json
import requests
import zipfile
import io
import flask_cors

from flask import Flask
from flask import Response
from flask import request
import ee

import config

# if __name__ == '__main__':
#    import config
# else:
#    from . import config


app = Flask(__name__)
# Initialize the EE API.
# Use our App Engine service account's credentials.
EE_CREDENTIALS = ee.ServiceAccountCredentials(config.EE_ACCOUNT,
                                              config.EE_PRIVATE_KEY_FILE)
ee.Initialize(EE_CREDENTIALS)

# HydroBASINS level 5
basins = {
    5: ee.FeatureCollection('users/gena/HydroEngine/hybas_lev05_v1c'),
    6: ee.FeatureCollection('users/gena/HydroEngine/hybas_lev06_v1c'),
    7: ee.FeatureCollection('users/gena/HydroEngine/hybas_lev07_v1c'),
    8: ee.FeatureCollection('users/gena/HydroEngine/hybas_lev08_v1c'),
    9: ee.FeatureCollection('users/gena/HydroEngine/hybas_lev09_v1c'),
}

# HydroSHEDS rivers, 15s
rivers = ee.FeatureCollection('users/gena/HydroEngine/riv_15s_lev05')

# HydroLAKES
lakes = ee.FeatureCollection('users/gena/HydroLAKES_polys_v10')

# graph index
index = ee.FeatureCollection('users/gena/HydroEngine/hybas_lev06_v1c_index')

monthly_water = ee.ImageCollection('JRC/GSW1_0/MonthlyHistory')

# bathymetry
bathymetry_vaklodingen = ee.ImageCollection('users/gena/vaklodingen')
bathymetry_jetski = ee.ImageCollection(
    'users/gena/eo-bathymetry/sandengine_jetski')
bathymetry_lidar = ee.ImageCollection('users/gena/eo-bathymetry/rws_lidar')


def get_upstream_catchments(level):
    if level != 6:
        raise Exception('Currently, only level 6 is supported for upstream catchments')

    def _get_upstream_catchments(basin_source) -> ee.FeatureCollection:
        hybas_id = ee.Number(basin_source.get('HYBAS_ID'))
        upstream_ids = index.filter(
            ee.Filter.eq('hybas_id', hybas_id)).aggregate_array('parent_from')
        upstream_basins = basins[level].filter(
            ee.Filter.inList('HYBAS_ID', upstream_ids)).merge(
            ee.FeatureCollection([basin_source]))

        return upstream_basins

    return _get_upstream_catchments


def number_to_string(i):
    return ee.Number(i).format('%d')


# TODO: merge all bathymetric data sets (GEBCO, EMODnet, Vaklodingen, JetSki, NOAA LiDAR, ...)
# TODO: regurn multiple profiles
# TODO: add an argument in get_raster_profile(): reducer (max, min, mean, ...)
def reduceImageProfile(image, line, reducer, scale):
    length = line.length()
    distances = ee.List.sequence(0, length, scale)
    lines = line.cutLines(distances).geometries();

    def generate_line_segment(l):
        l = ee.List(l)
        geom = ee.Geometry(l.get(0))
        distance = ee.Geometry(l.get(1))

        geom = ee.Algorithms.GeometryConstructors.LineString(
            geom.coordinates())

        return ee.Feature(geom, {'distance': distance})

    lines = lines.zip(distances).map(generate_line_segment)
    lines = ee.FeatureCollection(lines)

    # reduce image for every segment
    band_names = image.bandNames()

    return image.reduceRegions(lines, reducer.setOutputs(band_names), scale)


@app.route('/get_image_urls', methods=['GET', 'POST'])
@flask_cors.cross_origin()
def api_get_image_urls():
    r = request.get_json()
    dataset = r[
        'dataset']  # bathymetry_jetski | bathymetry_vaklodingen | dem_srtm | ...
    t_begin = ee.Date(r['begin_date'])
    t_end = ee.Date(r['end_date'])
    t_step = r['step']
    t_interval = r['interval']

    t_step_units = 'day'
    t_interval_unit = 'day'

    # TODO: let t_count be dependent on begin_date - end_date
    # TODO: Make option for how the interval is chosen (now only forward)
    t_count = 10

    rasters = {
        'bathymetry_jetski': bathymetry_jetski,
        'bathymetry_vaklodingen': bathymetry_vaklodingen,
        'bathymetry_lidar': bathymetry_lidar
    }

    colorbar_min = {
        'bathymetry_jetski': -12,
        'bathymetry_vaklodingen': -12,
        'bathymetry_lidar': -1200
    }

    colorbar_max = {
        'bathymetry_jetski': 7,
        'bathymetry_vaklodingen': 7,
        'bathymetry_lidar': 700
    }

    sandengine_pallete = '''#000033,#000037,#00003a,#00003e,#000042,#000045,#000049,#00004d,#000050,#000054,#000057,#00005b,#00005f,#000062,#000066,#010268,#03036a,#04056c,#05076e,#070971,#080a73,#0a0c75,#0b0e77,#0c1079,#0e117b,#0f137d,#10157f,#121781,#131884,#141a86,#161c88,#171e8a,#191f8c,#1a218e,#1b2390,#1d2492,#1e2695,#1f2897,#212a99,#222b9b,#242d9d,#252f9f,#2a35a2,#2e3ca6,#3342a9,#3848ac,#3c4faf,#4155b3,#465cb6,#4a62b9,#4f68bc,#546fc0,#5875c3,#5d7bc6,#6282ca,#6688cd,#6b8fd0,#7095d3,#749bd7,#79a2da,#7ea8dd,#82aee0,#87b5e4,#8cbbe7,#90c2ea,#95c8ed,#9acef1,#9ed5f4,#a3dbf7,#a8e1fa,#9edef7,#94daf4,#8ad6f0,#80d2ed,#84cacb,#87c2a9,#8bba87,#8eb166,#92a944,#95a122,#999900,#a4a50b,#afb116,#babd21,#c5c92c,#d0d537,#dce142,#e7ec4d,#f2f857,#f3f658,#f3f359,#f4f15a,#f5ee5b,#f6eb5c,#f6e95d,#f7e65d,#f8e35e,#f9e15f,#fade60,#fadc61,#fbd962,#fcd663,#fdd463,#fdd164,#fecf65,#ffcc66,#fdc861,#fcc55d,#fbc158,#f9be53,#f7ba4f,#f6b64a,#f5b346,#f3af41,#f1ac3c,#f0a838,#efa433,#eda12e,#eb9d2a,#ea9a25,#e99620,#e7931c,#e58f17,#e48b13,#e3880e,#e18409,#df8105,#de7d00'''

    raster = rasters[dataset]

    def generate_average_image(i):
        b = t_begin.advance(ee.Number(t_step).multiply(i), t_step_units)
        e = b.advance(t_interval, t_interval_unit)

        images = raster.filterDate(b, e)

        reducer = ee.Reducer.mean()

        return images.reduce(reducer).set('begin', b).set('end', e)

    def generate_image_info(image):
        image = ee.Image(image)
        m = image.getMapId(
            {'min': colorbar_min[dataset], 'max': colorbar_max[dataset],
             'palette': sandengine_pallete})

        mapid = m.get('mapid')
        token = m.get('token')

        url = 'https://earthengine.googleapis.com/map/{0}/{{z}}/{{x}}/{{y}}?token={1}'.format(
            id, token)

        begin = image.get('begin').getInfo()

        end = image.get('end').getInfo()

        return {'mapid': mapid, 'token': token, 'url': url, 'begin': begin,
                'end': end}

    images = ee.List.sequence(0, t_count).map(generate_average_image)

    infos = [generate_image_info(images.get(i)) for i in
             range(images.size().getInfo())]

    resp = Response(json.dumps(infos), status=200, mimetype='application/json')

    return resp


@app.route('/get_raster_profile', methods=['GET', 'POST'])
@flask_cors.cross_origin()
def api_get_raster_profile():
    r = request.get_json()

    polyline = ee.Geometry(r['polyline'])
    scale = float(r['scale'])
    dataset = r[
        'dataset']  # bathymetry_jetski | bathymetry_vaklodingen | dem_srtm | ...
    begin_date = r['begin_date']
    end_date = r['end_date']

    rasters = {
        'bathymetry_jetski': bathymetry_jetski,
        'bathymetry_vaklodingen': bathymetry_vaklodingen,
        'bathymetry_lidar': bathymetry_lidar
    }

    raster = rasters[dataset]

    if begin_date:
        raster = raster.filterDate(begin_date, end_date)

    reducer = ee.Reducer.mean()

    raster = raster.reduce(reducer)

    data = reduceImageProfile(raster, polyline, reducer, scale).getInfo()

    # fill response
    resp = Response(json.dumps(data), status=200, mimetype='application/json')

    return resp


@app.route('/get_catchments', methods=['GET', 'POST'])
def api_get_catchments():
    region = ee.Geometry(request.json['region'])
    region_filter = request.json['region_filter']
    catchment_level = request.json['catchment_level']

    if region_filter == 'region':
        raise Exception(
            'Value is not supported, use either catchments-upstream '
            'or catchments-intersection')

    selection = basins[catchment_level].filterBounds(region)

    if region_filter == 'catchments-upstream':
        print('Getting upstream catchments ..')

        # for every selection, get and merge upstream
        upstream_catchments = ee.FeatureCollection(
            selection.map(get_upstream_catchments(catchment_level))) \
            .flatten().distinct('HYBAS_ID')
    else:
        print('Getting intersected catchments ..')

        upstream_catchments = selection

    # dissolve output
    # TODO: dissolve output

    # get GeoJSON
    data = upstream_catchments.getInfo()  # TODO: use ZIP to prevent 5000 feature limit

    # fill response
    resp = Response(json.dumps(data), status=200, mimetype='application/json')

    return resp


@app.route('/get_rivers', methods=['GET', 'POST'])
def api_get_rivers():
    region = ee.Geometry(request.json['region'])
    region_filter = request.json['region_filter']
    catchment_level = request.json['catchment_level']

    # TODO: add support for region-only

    selected_catchments = basins[catchment_level].filterBounds(region)

    if region_filter == 'catchments_upstream':
        # for every selection, get and merge upstream catchments
        selected_catchments = ee.FeatureCollection(
            selected_catchments.map(get_upstream_catchments(catchment_level))) \
            .flatten().distinct('HYBAS_ID')

    # get ids
    upstream_catchment_ids = ee.List(
        selected_catchments.aggregate_array('HYBAS_ID')).map(number_to_string)

    # query rivers
    selected_rivers = rivers \
        .filter(ee.Filter.inList('HYBAS_ID', upstream_catchment_ids)) \
        .select(['ARCID', 'UP_CELLS', 'HYBAS_ID'])

    # filter upstream branches
    if 'filter_upstream_gt' in request.json:
        filter_upstream = int(request.json['filter_upstream_gt'])
        print(
            'Filtering upstream branches, limiting by {0} number of cells'.format(
                filter_upstream))
        selected_rivers = selected_rivers.filter(
            ee.Filter.gte('UP_CELLS', filter_upstream))

    # create response
    url = selected_rivers.getDownloadURL('json')

    data = {'url': url}

    return Response(json.dumps(data), status=200, mimetype='application/json')

    # data = selected_rivers.getInfo()  # TODO: use ZIP to prevent 5000 features limit
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
    region = ee.Geometry(request.json['region'])
    id_only = bool(request.json['id_only'])

    # query lakes
    selected_lakes = ee.FeatureCollection(lakes.filterBounds(region))

    if id_only:
        print('Getting lake ids only ... ')
        ids = selected_lakes.aggregate_array('Hylak_id')
        print(ids.getInfo())

        return Response(json.dumps(ids.getInfo()), status=200,
                        mimetype='application/json')

    # create response
    url = selected_lakes.getDownloadURL('json')

    data = {'url': url}

    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/get_lake_by_id', methods=['GET', 'POST'])
def get_lake_by_id():
    lake_id = int(request.json['lake_id'])

    lake = ee.Feature(ee.FeatureCollection(
        lakes.filter(ee.Filter.eq('Hylak_id', lake_id))).first())

    return Response(json.dumps(lake.getInfo()), status=200,
                    mimetype='application/json')


def get_lake_water_area(lake_id, scale):
    f = ee.Feature(lakes.filter(ee.Filter.eq('Hylak_id', lake_id)).first())

    def get_monthly_water_area(i):
        # get water mask
        water = i.clip(f).eq(2)

        s = scale
        if not scale:
            # estimate scale from reservoir surface area, currently
            coords = ee.List(f.geometry().bounds().transform('EPSG:3857',
                                                             30).coordinates().get(
                0))
            ll = ee.List(coords.get(0))
            ur = ee.List(coords.get(2))
            width = ee.Number(ll.get(0)).subtract(ur.get(0)).abs()
            height = ee.Number(ll.get(1)).subtract(ur.get(1)).abs()
            size = width.max(height)

            MAX_PIXEL_COUNT = 1000

            s = size.divide(MAX_PIXEL_COUNT).max(30)

            print('Automatically estimated scale is: ' + str(s.getInfo()))

        # compute water area
        water_area = water.multiply(ee.Image.pixelArea()).reduceRegion(
            ee.Reducer.sum(), f.geometry(), s).values().get(0)

        return ee.Feature(None, {'time': i.date().millis(),
                                 'water_area': water_area})

    area = monthly_water.map(get_monthly_water_area)

    area_values = area.aggregate_array('water_area')
    area_times = area.aggregate_array('time')

    return {'time': area_times.getInfo(), 'water_area': area_values.getInfo()}


@app.route('/get_lake_time_series', methods=['GET', 'POST'])
def api_get_lake_time_series():
    lake_id = int(request.json['lake_id'])
    variable = str(request.json['variable'])

    scale = None
    if 'scale' in request.json:
        scale = int(request.json['scale'])

    if variable == 'water_area':
        ts = get_lake_water_area(lake_id, scale)

        return Response(json.dumps(ts), status=200,
                        mimetype='application/json')

    return Response('Unknown variable', status=404,
                    mimetype='application/json')


@app.route('/get_raster', methods=['GET', 'POST'])
def api_get_raster():
    variable = request.json['variable']
    region = ee.Geometry(request.json['region'])
    cell_size = float(request.json['cell_size'])
    crs = request.json['crs']
    region_filter = request.json['region_filter']
    catchment_level = request.json['catchment_level']

    if region_filter == 'catchments-upstream':
        selection_basins = basins[catchment_level].filterBounds(region)

        # for every selection, get and merge upstream
        region = ee.FeatureCollection(
            selection_basins.map(get_upstream_catchments(catchment_level))) \
            .flatten().distinct('HYBAS_ID').geometry()

        region = region.bounds()

    if region_filter == 'catchments-intersection':
        region = basins[catchment_level].filterBounds(region)

        region = region.geometry().bounds()


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
