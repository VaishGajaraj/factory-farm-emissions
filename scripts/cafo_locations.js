// CAFO Facility Locations for Chesapeake Bay
var cafoLocations = ee.FeatureCollection([
  ee.Feature(ee.Geometry.Point([-75.823, 38.521]), {
    'facility_id': 'MD_DAIRY_001',
    'name': 'Chesapeake Gold Dairy',
    'type': 'dairy',
    'animal_units': 2500,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-76.456, 38.234]), {
    'facility_id': 'MD_DAIRY_002',
    'name': 'Eastern Shore Farms',
    'type': 'dairy',
    'animal_units': 1800,
    'isolation_score': 0.50
  }),
  ee.Feature(ee.Geometry.Point([-75.234, 38.745]), {
    'facility_id': 'MD_POULTRY_001',
    'name': 'Delmarva Poultry Complex A',
    'type': 'poultry',
    'animal_units': 125000,
    'isolation_score': 1.00
  }),
  ee.Feature(ee.Geometry.Point([-75.987, 38.123]), {
    'facility_id': 'MD_POULTRY_002',
    'name': 'Somerset Broiler Farm',
    'type': 'poultry',
    'animal_units': 75000,
    'isolation_score': 0.50
  }),
  ee.Feature(ee.Geometry.Point([-76.123, 38.876]), {
    'facility_id': 'MD_BEEF_001',
    'name': 'Chesapeake Cattle Co',
    'type': 'beef',
    'animal_units': 1500,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-75.345, 38.654]), {
    'facility_id': 'DE_POULTRY_001',
    'name': 'Sussex Poultry Farm A',
    'type': 'poultry',
    'animal_units': 100000,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-75.385, 38.707]), {
    'facility_id': 'DE_POULTRY_002',
    'name': 'Georgetown Chicken Farm',
    'type': 'poultry',
    'animal_units': 80000,
    'isolation_score': 0.50
  }),
  ee.Feature(ee.Geometry.Point([-75.527, 38.892]), {
    'facility_id': 'DE_DAIRY_001',
    'name': 'First State Dairy',
    'type': 'dairy',
    'animal_units': 3200,
    'isolation_score': 1.00
  }),
  ee.Feature(ee.Geometry.Point([-75.234, 38.756]), {
    'facility_id': 'DE_SWINE_001',
    'name': 'Delaware Pork Producers',
    'type': 'swine',
    'animal_units': 5000,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-75.632, 37.876]), {
    'facility_id': 'VA_POULTRY_001',
    'name': 'Accomack Broilers',
    'type': 'poultry',
    'animal_units': 90000,
    'isolation_score': 1.00
  }),
  ee.Feature(ee.Geometry.Point([-75.987, 37.234]), {
    'facility_id': 'VA_POULTRY_002',
    'name': 'Northampton Farms',
    'type': 'poultry',
    'animal_units': 65000,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-76.234, 37.567]), {
    'facility_id': 'VA_DAIRY_001',
    'name': 'Virginia Eastern Dairy',
    'type': 'dairy',
    'animal_units': 2200,
    'isolation_score': 0.50
  }),
  ee.Feature(ee.Geometry.Point([-76.068, 39.049]), {
    'facility_id': 'MD_POULTRY_003',
    'name': 'Queen Anne's Poultry',
    'type': 'poultry',
    'animal_units': 55000,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-76.175, 38.773]), {
    'facility_id': 'MD_DAIRY_003',
    'name': 'Talbot County Dairy',
    'type': 'dairy',
    'animal_units': 1600,
    'isolation_score': 0.50
  }),
  ee.Feature(ee.Geometry.Point([-75.428, 38.915]), {
    'facility_id': 'DE_POULTRY_003',
    'name': 'Milford Chicken Complex',
    'type': 'poultry',
    'animal_units': 70000,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-75.678, 38.456]), {
    'facility_id': 'MD_MIXED_001',
    'name': 'Diversified Farms LLC',
    'type': 'mixed',
    'animal_units': 3500,
    'isolation_score': 0.50
  }),
  ee.Feature(ee.Geometry.Point([-75.139, 38.545]), {
    'facility_id': 'DE_BEEF_001',
    'name': 'Sussex Beef Operations',
    'type': 'beef',
    'animal_units': 1200,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-76.345, 37.789]), {
    'facility_id': 'VA_MIXED_001',
    'name': 'Tidewater Agricultural',
    'type': 'mixed',
    'animal_units': 2800,
    'isolation_score': 1.00
  }),
  ee.Feature(ee.Geometry.Point([-76.789, 38.234]), {
    'facility_id': 'MD_SWINE_001',
    'name': 'Maryland Pork Farm',
    'type': 'swine',
    'animal_units': 3000,
    'isolation_score': 0.80
  }),
  ee.Feature(ee.Geometry.Point([-75.571, 38.557]), {
    'facility_id': 'DE_POULTRY_004',
    'name': 'Laurel Broiler Farm',
    'type': 'poultry',
    'animal_units': 85000,
    'isolation_score': 0.50
  })
]);
