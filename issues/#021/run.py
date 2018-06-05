import json
import hydroengine as he

region_path = 'region.json'

with open(region_path) as region_file:
  region = json.load(region_file)

# query water mask
s = he.get_water_mask(region)

print('Water mask: ')
print(s)


