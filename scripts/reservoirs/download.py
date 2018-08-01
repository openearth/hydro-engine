import os
import json
import pandas as pd
import hydroengine as he

# download MENA.json using users/gena/eo-reservoirs/MENA_waterbodies.js
# gs://hydro-engine/waterbodies/MENA.json

path = '../../data/reservoirs/HydroLAKES_Niger_not_MENA.json'
# path = '../../data/reservoirs/MENA.json'

with open(path) as f:
  j = json.loads(f.read())


bad = [152, 156, 180279]

for lake_id in [f['properties']['Hylak_id'] for f in j['features']]:
  path = '../../data/reservoirs/surface-water-area-v1/water_area_' + str(lake_id).zfill(15) + '.csv'

  if lake_id in bad:
    print(path + ', bad, skipping ...')
    continue

  if os.path.exists(path):
    print(path + ', already exists, skipping ...')
    continue
  else:
    print(path + ', downloading ...')

  variable = 'water_area'
  ts = he.get_lake_time_series(lake_id, variable)
  d = pd.DataFrame(ts)
  d = d[d['water_area'] != 0]
  d['time'] = pd.to_datetime(d['time'], unit='ms')
  d.to_csv(path)

  

