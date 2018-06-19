if not exist ../../data/reservoirs (
  md ../../data/reservoirs
)

gsutil cp gs://hydro-engine/reservoirs/MENA.json ../../data/reservoirs/MENA.json

if not exist ../../data/reservoirs/surface-water-area-v1 (
  md ../../data/reservoirs/surface-water-area-v1
)

gsutil -m cp gs://hydro-engine/reservoirs/surface-water-area-v1/*.csv ./surface-water-area-v1/