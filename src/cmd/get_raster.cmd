@echo off

echo Retrieving elevation ...

.\bin\curl -H "Content-Type: application/json" -X POST -d @get_raster.json http://localhost:8080/get_raster -o get_raster.tif
