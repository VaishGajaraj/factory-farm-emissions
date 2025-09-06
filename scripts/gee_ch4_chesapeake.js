// RReverie Chesapeake CH4 monthly composites (Sentinel-5P TROPOMI)
// Usage: Paste into Google Earth Engine Code Editor and Run
// Output: Monthly composites (last 12 months) and a time-series chart over Chesapeake/Delmarva

// --- Region: Chesapeake Bay watershed (approx bbox covering Delmarva & Bay) ---
var region = ee.Geometry.Rectangle([-77.8, 36.5, -74.5, 40.3], null, false);
Map.centerObject(region, 7);

// --- Time window: last 12 months ---
var now = ee.Date(Date.now());
var start = now.advance(-12, 'month');
var end = now;

// --- Dataset: S5P OFFL L3 CH4 (XCH4)
// Band of interest: 'CH4_column_volume_mixing_ratio_dry_air_bias_corrected' (ppb)
var s5p = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_CH4')
  .filterDate(start, end)
  .filterBounds(region);

// Build month windows from start → start+11 months
var months = ee.List.sequence(0, 11).map(function(i) {
  i = ee.Number(i);
  var monthStart = start.advance(i, 'month');
  var monthEnd = monthStart.advance(1, 'month');
  var label = monthStart.format('YYYY-MM');
  return ee.Dictionary({start: monthStart, end: monthEnd, label: label});
});

// Build monthly mean images
var monthlyImages = months.map(function(d) {
  d = ee.Dictionary(d);
  var s = ee.Date(d.get('start'));
  var e = ee.Date(d.get('end'));
  var label = ee.String(d.get('label'));
  var img = s5p
    .filterDate(s, e)
    .select('CH4_column_volume_mixing_ratio_dry_air_bias_corrected')
    .mean()
    .set('system:time_start', s.millis())
    .set('label', label);
  return img;
});

var monthlyCol = ee.ImageCollection.fromImages(monthlyImages).sort('system:time_start');

// Visualization parameters: ppb range; adjust as needed
var vis = {min: 1800, max: 2000, palette: ['2c7bb6','abd9e9','ffffbf','fdae61','d7191c']};

// Add first and last month for quick look
var first = ee.Image(monthlyCol.first());
var last = ee.Image(monthlyCol.sort('system:time_start', false).first());
Map.addLayer(first.clip(region), vis, 'First month');
Map.addLayer(last.clip(region), vis, 'Last month');

// Add boundary (optional)
Map.addLayer(region, {color: '000000'}, 'Chesapeake bbox', false);

// Time series chart over region mean
var chart = ui.Chart.image.series({
  imageCollection: monthlyCol.select('CH4_column_volume_mixing_ratio_dry_air_bias_corrected'),
  region: region,
  reducer: ee.Reducer.mean(),
  scale: 20000,
  xProperty: 'system:time_start'
}).setOptions({
  title: 'Chesapeake XCH4 (last 12 months)',
  vAxis: {title: 'ppb'},
  hAxis: {title: 'Month'},
  legend: {position: 'none'}
});
print(chart);

// Optional export example (last month) to Drive
// var exportImg = last.clip(region).reproject({crs: 'EPSG:4326', scale: 10000});
// Export.image.toDrive({
//   image: exportImg,
//   description: 'Chesapeake_XCH4_last_month',
//   fileNamePrefix: 'chesapeake_xch4_last_month',
//   region: region,
//   scale: 10000,
//   maxPixels: 1e13
// });
