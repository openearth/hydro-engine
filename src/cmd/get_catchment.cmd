@echo off

echo Retrieving catchment boundary ...

.\bin\curl -H "Content-Type: application/json" -X POST -d @query.json http://hydro-earth.appspot.com/get_catchment -o results.json
rem .\bin\curl -H "Content-Type: application/json" -X POST -d @query.json http://localhost:8080/get_catchment -o results.json
