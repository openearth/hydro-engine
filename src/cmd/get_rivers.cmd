@echo off

echo Querying and downloading rivers ...

.\bin\curl -H "Content-Type: application/json" -X POST -d @get_rivers.json http://localhost:8080/get_rivers -o get_rivers_results.json
