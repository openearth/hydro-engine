@echo off

echo Retrieving catchment boundary ...

rem curl -H "Content-Type: application/json" -X POST -d @query.json http://hydro-earth.appspot.com/get_catchment -o results.json
.\bin\curl -H "Content-Type: application/json" -X POST -d @query.json http://localhost:8080/get_catchment -o results.json
