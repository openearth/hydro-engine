import argparse
import requests
import json
import shutil
import zipfile
import tempfile
import os
import os.path

# SERVER_URL = 'http://localhost:8080'
SERVER_URL = 'http://hydro-engine.appspot.com'

def download_catchments(region, path):
    data = {'type': 'get_catchments', 'bounds': region, 'dissolve': True}
    r = requests.post(SERVER_URL + '/get_catchments', json=data)

    with open(path, 'w') as file:
        file.write(r.text)


def download_rivers(region, path, filter_upstream_gt):
    data = {'type': 'get_rivers', 'bounds': region}

    if filter_upstream_gt:
        data['filter_upstream_gt'] = filter_upstream_gt

    r = requests.post(SERVER_URL + '/get_rivers', json=data)

    # download from url
    r = requests.get(json.loads(r.text)['url'], stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

def get_lake_time_series(lake_id, variable, scale=0):
    data = {'type': 'get_lake_time_series', 'lake_id': lake_id, 'variable': variable, 'scale': scale}
   
    r = requests.post(SERVER_URL + '/get_lake_time_series', json=data)

    return json.loads(r.text)

def download_lake_variable(lake_id, variable, path, scale):
    if variable == 'water_area':
        ts = get_lake_time_series(lake_id, variable, scale)
        with open(path, 'w') as f:
            json.dump(ts, f)
    else:
        print('Only \'water_area\' can be downloaded for now')

def get_lakes(region):
    data = {'type': 'get_lakes', 'bounds': region, 'id_only': False}

    r = requests.post(SERVER_URL + '/get_lakes', json=data)

    r = requests.get(json.loads(r.text)['url'], stream=True)
    if r.status_code == 200:
        r.raw.decode_content = True
        return json.loads(r.raw.data.decode('utf-8'))

def get_lake_ids(region):
    data = {'type': 'get_lakes', 'bounds': region, 'id_only': True}

    r = requests.post(SERVER_URL + '/get_lakes', json=data)

    return json.loads(r.text)

def get_lake_by_id(lake_id):
    data = {'type': 'get_lake_by_id', 'lake_id': lake_id}

    r = requests.post(SERVER_URL + '/get_lake_by_id', json=data)

    return json.loads(r.text)


def download_lakes(region, path, id_only):
    if id_only:
        ids = get_lake_ids(region)

        with open(path, 'w') as f:
            json.dump(ids, f)

        return

    data = {'type': 'get_lakes', 'bounds': region, 'id_only': id_only}

    r = requests.post(SERVER_URL + '/get_lakes', json=data)

    # download from url
    r = requests.get(json.loads(r.text)['url'], stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

def download_raster(region, path, variable, cell_size, crs):
    path_name = os.path.splitext(path)[0]

    data = {'type': 'get_raster', 'bounds': region, 'variable': variable, 'cell_size': cell_size, 'crs': crs}

    r = requests.post(SERVER_URL + '/get_raster_profile', json=data)

    # download from url
    r = requests.get(json.loads(r.text)['url'], stream=True)
    if r.status_code == 200:
        # download zip into a temporary file
        f = tempfile.NamedTemporaryFile(delete=False)
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
        f.close()

        temp_dir = tempfile.mkdtemp()

        # unzip and rename both tfw and tif
        zip = zipfile.ZipFile(f.name, 'r')
        items = zip.namelist()
        zip.extractall(temp_dir)
        zip.close()

        # move extracted files to the target path
        src_tfw = os.path.join(temp_dir, items[0])
        dst_tfw = path_name + '.tfw'
        if os.path.exists(dst_tfw):
            os.remove(dst_tfw)
        os.rename(src_tfw, dst_tfw)

        src_tif = os.path.join(temp_dir, items[1])
        if os.path.exists(path):
            os.remove(path)
        os.rename(src_tif, path)

        # clean-up
        os.rmdir(temp_dir)
        os.remove(f.name)

def download_raster_profile(region, path, variable, scale):
    data = {'type': 'get_raster_profile', 'polyline': region, 'variable': variable, 'scale': scale}

    r = requests.post(SERVER_URL + '/get_raster_profile', json=data)

    # download from url
    profile = json.loads(r.text)
    if r.status_code == 200:
        with open(path, 'w') as f:
            json.dump(profile, f)


def main():
    parser = argparse.ArgumentParser(description='Download hydrological model input data.')

    # TODO: rename region to geometry. Can be polygon / polyline / point
    parser.add_argument('region', nargs='?',
                        help='Input region GeoJSON file, used to detect upstream catchment boundaries')
    parser.add_argument('--get-catchments', metavar='PATH',
                        help='Download catchments to PATH')
    parser.add_argument('--get-rivers', metavar='PATH',
                        help='Download rivers to PATH')
    parser.add_argument('--get-lakes', metavar='PATH',
                        help='Download lake to PATH')
    parser.add_argument('--id-only', action='store_true',
                        help='Return only feature ids')
    parser.add_argument('--scale', metavar='VALUE',
                        help='When downloading lake time series or performing other geospatial operations - scale can be optionally specified')
    parser.add_argument('--get-lake-variable', metavar=('LAKE-ID', 'VARIABLE', 'PATH'), nargs=3,
                        help='Download lake variable to PATH in JSON format, VARIABLE is currently only \'water_area\', LAKE-ID can be obtained using --id-only or from a full lake information')
    parser.add_argument('--filter-upstream-gt', metavar='VALUE',
                        help='When downloading rivers, limit number of upstream cells to VALUE')
    parser.add_argument('--get-raster', metavar=('VARIABLE', 'PATH', 'CELL_SIZE', 'CRS'), nargs=4,
                        help='Download VARIABLE to PATH as a raster, clipped to the upstream catchment boundaries'
                        'Cell size for output rasters is in meters.'
                        'Coordinate Reference System needs to be given as an EPSG code, for example: EPSG:4326',
                        type=str)
    parser.add_argument('--get-raster-profile', metavar=('VARIABLE', 'PATH', 'SCALE'), nargs=3,
                        help='Download VARIABLE to PATH as a raster, clipped to the upstream catchment boundaries'
                        'VARIABLE can be one of: bathymetry | elevation'
                        'PATH if the name of output file'
                        'SCALE, defined in meters, is used to split input line into segments used to sample raster image.',
                        type=str)

    args = parser.parse_args()

    region_path = args.region
    filter_upstream_gt = args.filter_upstream_gt
    id_only = args.id_only
    scale = args.scale

    if not scale:
        scale = 0

    if region_path:
        with open(region_path) as region_file:
            region = json.load(region_file)

    if args.get_catchments:
        path = args.get_catchments
        print('Downloading catchments to {0} ...'.format(path))
        download_catchments(region, path)

    if args.get_rivers:
        path = args.get_rivers
        print('Downloading rivers to {0} ...'.format(path))
        download_rivers(region, path, filter_upstream_gt)

    if args.get_lakes:
        path = args.get_lakes
        print('Downloading lakes to {0} ...'.format(path))
        download_lakes(region, path, id_only)

    if args.get_lake_variable:
        lake_id = args.get_lake_variable[0]
        variable = args.get_lake_variable[1]
        path = args.get_lake_variable[2]
        print('Downloading lake variable to {0} ...'.format(path))
        download_lake_variable(lake_id, variable, path, scale)

    if args.get_raster:
        variable = args.get_raster[0]
        path = args.get_raster[1]
        cell_size = args.get_raster[2]
        crs = args.get_raster[3]
        print('Downloading raster variable {0} to {1} ...'.format(variable, path))
        download_raster(region, path, variable, cell_size, crs)

    if args.get_raster_profile:
        variable = args.get_raster_profile[0]
        path = args.get_raster_profile[1]
        scale = args.get_raster_profile[2]
        print('Downloading raster profile for variable {0} to {1} ...'.format(variable, path))
        download_raster_profile(region, path, variable, scale)

if __name__ == "__main__":
    main()
