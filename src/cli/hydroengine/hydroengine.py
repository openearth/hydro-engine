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

def download_lakes(region, path):
    data = {'type': 'get_lakes', 'bounds': region}

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

    r = requests.post(SERVER_URL + '/get_raster', json=data)

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

def main():
    parser = argparse.ArgumentParser(description='Download hydrological model input data.')

    parser.add_argument('region',
                        help='Input region GeoJSON file, used to detect upstream catchment boundaries')
    parser.add_argument('--get-catchments', metavar='PATH',
                        help='Download catchments to PATH')
    parser.add_argument('--get-rivers', metavar='PATH',
                        help='Download rivers to PATH')
    parser.add_argument('--get-lakes', metavar='PATH',
                        help='Download lake to PATH')
    parser.add_argument('--filter-upstream-gt', metavar='VALUE',
                        help='When downloading rivers, limit number of upstream cells to VALUE')
    parser.add_argument('--get-raster', metavar=('VARIABLE', 'PATH', 'CELL_SIZE', 'CRS'), nargs=4,
                        help='Download VARIABLE to PATH as a raster, clipped to the upstream catchment boundaries'
                        'Cell size for output rasters is in meters.'
                        'Coordinate Reference System needs to be given as an EPSG code, for example: EPSG:4326',
                        type=str)

    args = parser.parse_args()

    region_path = args.region
    filter_upstream_gt = args.filter_upstream_gt

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
        download_lakes(region, path)

    if args.get_raster:
        variable = args.get_raster[0]
        path = args.get_raster[1]
        cell_size = args.get_raster[2]
        crs = args.get_raster[3]
        print('Downloading raster variable {0} to {1} ...'.format(variable, path))
        download_raster(region, path, variable, cell_size, crs)

if __name__ == "__main__":
    main()
