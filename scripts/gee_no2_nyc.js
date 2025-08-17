// RReverie NYC NO2 monthly composites (Sentinel-5P TROPOMI)
// Usage: Paste into Google Earth Engine Code Editor and Run
// Output: Monthly composites (last 12 months) and a time-series chart over NYC region

// --- Region: NYC metro bounding box (adjust if needed) ---
var region = ee.Geometry.Rectangle([-74.35, 40.45, -73.55, 41.10], null, false);
Map.centerObject(region, 9);

// --- Time window: last 12 months ---
var now = ee.Date(Date.now());
var start = now.advance(-12, 'month');
var end = now;

// --- Dataset: S5P OFFL L3 NO2 (daily gridded product) ---
// Band of interest: 'tropospheric_NO2_column_number_density' (mol/m^2)
var s5p = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
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
    .select('tropospheric_NO2_column_number_density')
    .mean()
    .set('system:time_start', s.millis())
    .set('label', label);
  return img;
});

var monthlyCol = ee.ImageCollection.fromImages(monthlyImages).sort('system:time_start');

// Visualization parameters
var vis = {min: 0, max: 0.0002, palette: ['2c7bb6','abd9e9','ffffbf','fdae61','d7191c']};

// Add first and last month for quick look
var first = ee.Image(monthlyCol.first());
var last = ee.Image(monthlyCol.sort('system:time_start', false).first());
Map.addLayer(first.clip(region), vis, 'First month');
Map.addLayer(last.clip(region), vis, 'Last month');

// Add boundary
Map.addLayer(region, {color: '000000'}, 'NYC bbox', false);

// Time series chart over region mean
var chart = ui.Chart.image.series({
  imageCollection: monthlyCol,
  region: region,
  reducer: ee.Reducer.mean(),
  scale: 10000,
  xProperty: 'system:time_start'
}).setOptions({
  title: 'NYC Tropospheric NO2 (last 12 months)',
  vAxis: {title: 'mol/m^2'},
  hAxis: {title: 'Month'},
  legend: {position: 'none'}
});
print(chart);

// Optional: browse all months as layers (can be heavy)
// monthlyCol.evaluate(function(col) {
//   col.features.forEach(function(f) {
//     var img = ee.Image(f.id);
//     var label = f.properties.label;
//     Map.addLayer(img.clip(region), vis, label, false);
//   });
// });

// Optional export (single month) to Drive — requires linking Drive in GEE
// var exportImg = last.clip(region).reproject({crs: 'EPSG:4326', scale: 5000});
// Export.image.toDrive({
//   image: exportImg,
//   description: 'NYC_NO2_last_month',
//   fileNamePrefix: 'nyc_no2_last_month',
//   region: region,
//   scale: 5000,
//   maxPixels: 1e13
// });
