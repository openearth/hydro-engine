Map.setOptions('SATELLITE')

var basins = ee.FeatureCollection('ft:1IHRHUiWkgPXOzwNweeM89CzPYSfokjLlz7_0OTQl')

basins = basins.map(function(f) {
  var isFirst = ee.Number(f.get('NEXT_DOWN')).neq(0)

  return f.set('is_first', isFirst)
})

var basinsImage = ee.Image().int().paint(basins2, 'is_first')
  .paint(basins, 2, 1)

Map.addLayer(basins.filter(ee.Filter.eq('COAST', 1)), {color:'blue'}, 'coast', true, 0.4)

Map.addLayer(basinsImage, {palette:['555555', '000000','ffff00'], min:0, max:2}, 'all (raster)', true, 0.5)

Map.addLayer(basins, {color:'white'}, 'all', false, 0.5)

var basinsLevel3l3 = ee.FeatureCollection('ft:13dShZ5yGqCEqk3dsJvYEL3lsa1hEmpMRldxK7aSa')
Map.addLayer(ee.Image().int().paint(l3, 0, 1), {palette:'ffffff'}, 'L3')

var current = basins.filterBounds(geometry)

var currentBasinLayer = ui.Map.Layer(current, {color:'black'}, 'current', false)

Map.layers().add(currentBasinLayer, false)


var colors = ['white', 'blue','green','red','yellow','orange','black', 'magenta']
var palette = ['ffffff', '0000ff','00ff00','ff0000','ffff00','ffa500','000000', '00ffff', 'ff00ff']
var source = current
var depth = palette.length

// upstream

var upstreamIds = index.filter(ee.Filter.eq('hybas_id', 1050022420)).aggregate_array('parent_from')
var upstreamBasins = basins.filter(ee.Filter.inList('HYBAS_ID', upstreamIds))
var upstreamBasinsLayer = ui.Map.Layer(upstreamBasins, {color:'green'}, 'upstream')
Map.layers().add(upstreamBasinsLayer)

Map.onClick(function(coords) {
  coords = ee.Dictionary(coords)
  var pt = ee.Geometry.Point([coords.get('lon'), coords.get('lat')])
  var current = basins.filterBounds(pt)
  var id = ee.Feature(current.first()).get('HYBAS_ID')
  var upstreamIds = index.filter(ee.Filter.eq('hybas_id', id)).aggregate_array('parent_from')

  var upstreamBasins = basins.filter(ee.Filter.inList('HYBAS_ID', upstreamIds)).merge(current)
  
  var upstreamBasinsImage = ee.Image()
    .paint(upstreamBasins, 0, 3)
    .paint(upstreamBasins, 1)
    
  
  upstreamBasinsLayer.setEeObject(upstreamBasinsImage)
  upstreamBasinsLayer.setVisParams({min:0, max:1, palette:['ffff00', 'ffff00'], opacity: 0.5})

  //currentBasinLayer.setEeObject(current)

  print(coords)
})

var rivers = ee.FeatureCollection('ft:15-WpLuijWukjWsjUral2RFZXx0IR7j2lLTAi8lR9')
//print(ui.Chart.feature.histogram(rivers, 'UP_CELLS'))

Map.addLayer(ee.Image().int().paint(rivers, 1, 1), {palette:['ffffff'], opacity: 0.5}, 'rivers')
Map.addLayer(ee.Image().int().paint(rivers.filter(ee.Filter.gt('UP_CELLS', 500000)), 1, 3), {palette:['aaaaff'], opacity: 0.5}, 'rivers (large)')
