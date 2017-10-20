import argparse
import requests
import json
import shutil

# SERVER_URL = 'http://localhost:8080'
SERVER_URL = 'http://hydro-engine.appspot.com'

parser = argparse.ArgumentParser(description='Download hydrological model input data.')

parser.add_argument('region',
                    help='Input region GeoJSON file, used to detect upstream catchment boundaries')
parser.add_argument('--get-catchments', metavar='PATH',
                    help='Download catchments to PATH')
parser.add_argument('--get-rivers', metavar='PATH',
                    help='Download rivers to PATH')
parser.add_argument('--filter-upstream-gt', metavar='VALUE',
                    help='When downloading rivers, limit number of upstream cells to VALUE')
parser.add_argument('--get-raster', metavar=('VARIABLE', 'PATH'), nargs=2,
                    help='Download VARIABLE to PATH as a raster, clipped to the upstream catchment boundaries',
                    type=str)

args = parser.parse_args()

region_path = args.region

with open(region_path) as region_file:
    region = json.load(region_file)


def download_catchments(path):
    data = {'type': 'get_catchments', 'bounds': region, 'dissolve': True}
    r = requests.post(SERVER_URL + '/get_catchments', json=data)

    with open(path, 'w') as file:
        file.write(r.text)


def download_rivers(path):
    data = {'type': 'get_rivers', 'bounds': region}

    if args.filter_upstream_gt:
        data['filter_upstream_gt'] = args.filter_upstream_gt

    r = requests.post(SERVER_URL + '/get_rivers', json=data)

    # download from url
    r = requests.get(json.loads(r.text)['catchment_rivers_url'], stream=True)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)


if args.get_catchments:
    print('Downloading catchments ...')
    download_catchments(args.get_catchments)

if args.get_rivers:
    print('Downloading rivers ...')
    download_rivers(args.get_rivers)
