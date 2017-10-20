**Hydro Engine** is a small service and a command-line tool built on top of ![Google Earth Engine](http://earthengine.google.com) that allows querying various hydrological variables, useful as an input for hydrological models.

All data can be queried for an input area or location (GeoJSON polygon geometry). A polygon may define, for example, a flood location. For example, in the figure below, a single point geometry is used to query upstream catchments and a drainage network, providing runoff water for that location.

<img src="https://github.com/Deltares/hydro-engine/blob/master/docs/example_query.png?raw=true" alt="Example" width="626" height="485">

Currently, the following functionality is supported:

* Query upstream catchments as a single or multiple polygons. Source: ![HydroBASINS](http://www.hydrosheds.org/page/hydrobasins)
* Query upstream drainage network as a line geometry. Source: ![HydroSHEDS](http://hydrosheds.org)

Additionally, the following raster variables can be also requested:

* dem [m] - in meters, source: 30m SRTM v4
* hand [m] - Height Above the Nearest Drainage (![HAND](http://global-hand.appspot.com))
* FirstZoneCapacity [-] - ?
* FirstZoneKsatVer [-] - ?
* FirstZoneMinCapacity [-] - ?
* InfiltCapSoil [-] - ?
* M [-] - ?
* PathFrac [-] - ?
* WaterFrac [-] - ?
* thetaS [-] - ?
* soil_type [-] - soil type, based on ?
* landuse [-] - land use type, based on MODIS 500m
* LAI01...LAI12 - leaf area index monthly climatology, source: ![eartH2Observe](http://www.earth2observe.eu/)

The command-line Python tool can be installed using the following commands:
```
> pip install hydro-engine
```

Then, data can be queried as:
```
> hydro-engine region.json --get-catchments catchments.json
> hydro-engine region.json --get-rivers rivers.json
> hydro-engine region.json --get-raster dem dem.tif 1000 EPSG:4326
```

Usage:

```
>hydro-engine.exe [-h]
                        [--get-catchments PATH]
                        [--get-rivers PATH] [--filter-upstream-gt VALUE]
                        [--get-raster VARIABLE PATH CELL_SIZE CRS]
                        region
```
