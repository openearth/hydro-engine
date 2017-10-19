@echo off

echo Retrieving catchment boundary ...

rem .\bin\curl -H "Content-Type: application/json" -X POST -d @query.json http://hydro-earth.appspot.com/get_catchment -o results_catchments.json
rem .\bin\curl -H "Content-Type: application/json" -X POST -d @query.json http://localhost:8080/get_catchments -o results_catchments.json

.\bin\curl -H "Content-Type: application/json" -X POST -d @query.json http://localhost:8080/get_rivers -o results_rivers.json
