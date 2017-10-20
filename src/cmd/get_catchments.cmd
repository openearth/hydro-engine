@echo off

echo Downloading upstream catchments ...
.\bin\curl -H "Content-Type: application/json" -X POST -d @get_catchments.json http://localhost:8080/get_catchments -o get_catchments_response.json
