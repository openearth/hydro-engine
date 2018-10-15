**Hydro Engine** is a small service and a command-line tool built on top of [Google Earth Engine](http://earthengine.google.com) that allows querying various hydrological variables, useful as an input for hydrological models.

[![Build Status](https://travis-ci.org/openearth/hydro-engine.svg?branch=master)](https://travis-ci.org/openearth/hydro-engine)

The command-line Python tool can be installed using the following commands:
```
> pip install hydroengine
```

Once the package is installed, you can use ```hydroengine``` command to download input data needed for your hydrological model.

Upstream catchments, rivers and various raster variables can be queried using following commands:

```
> hydroengine region.json --get-catchments catchments.json
> hydroengine region.json --get-rivers rivers.json
> hydroengine region.json --get-raster dem dem.tif 1000 EPSG:4326
> hydroengine region.json --get-lakes lakes.json
> hydroengine region.json --get-lake-variable 183160 water_area area.json
```

See [examples/run.sh](https://github.com/Deltares/hydro-engine/blob/master/examples/run.sh), showing how different data types can be downloaded.

All data types can be queried for an input area or location (GeoJSON polygon geometry). A polygon may define a flood location. For example, in the figure below, a single point near Houston is used to query upstream catchments and a drainage network, providing runoff water for that location.

<img src="https://github.com/Deltares/hydro-engine/blob/master/docs/example_query.png?raw=true" alt="Example" width="626" height="485">

Supported functionality:

* Querying upstream catchments as a single or multiple polygons. Source: [HydroBASINS](http://www.hydrosheds.org/page/hydrobasins)
* Querying upstream drainage network as polylines. Source: [HydroSHEDS](http://hydrosheds.org)
* Querying raster variables:
   * dem [m] - in meters, source: 30m SRTM v4
   * hand [m] - Height Above the Nearest Drainage ([HAND](http://global-hand.appspot.com))
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
   * LAI01...LAI12 - leaf area index monthly climatology, source: [eartH2Observe](http://www.earth2observe.eu/)

