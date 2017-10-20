rem python hydro-engine.py in/region.json --get-catchments out/catchments.json

rem python hydro-engine.py in/region.json --get-rivers out/rivers.json --filter-upstream-gt 1000

python hydro-engine.py in/region.json --get-raster dem out/dem.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster FirstZoneCapacity out/FirstZoneCapacity.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster FirstZoneKsatVer out/FirstZoneKsatVer.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster FirstZoneMinCapacity out/FirstZoneMinCapacity.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster InfiltCapSoil out/InfiltCapSoil.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster M out/M.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster PathFrac out/PathFrac.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster WaterFrac out/WaterFrac.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster thetaS out/thetaS.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster soil_type out/wflow_soil.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster landuse out/wflow_landuse.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI01 out/LAI01.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI02 out/LAI02.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI03 out/LAI03.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI04 out/LAI04.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI05 out/LAI05.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI06 out/LAI06.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI07 out/LAI07.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI08 out/LAI08.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI09 out/LAI09.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI10 out/LAI10.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI11 out/LAI11.tif 10000 EPSG:4326
python hydro-engine.py in/region.json --get-raster LAI12 out/LAI12.tif 10000 EPSG:4326
