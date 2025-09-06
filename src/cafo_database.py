"""
CAFO Database Management for Chesapeake Bay Region
Handles facility data, isolation scoring, and metadata
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CAFOFacility:
    """Data class for CAFO facility information"""
    facility_id: str
    name: str
    lat: float
    lon: float
    state: str
    county: str
    type: str  # dairy, poultry, beef, swine, mixed
    animal_units: int
    company: str
    isolation_km: float
    notes: str = ""
    
    @property
    def is_isolated(self) -> bool:
        """Facility is considered isolated if >10km from nearest neighbor"""
        return self.isolation_km > 10.0
    
    @property
    def isolation_score(self) -> float:
        """Score from 0-1 indicating isolation level"""
        if self.isolation_km >= 15:
            return 1.0
        elif self.isolation_km >= 10:
            return 0.8
        elif self.isolation_km >= 7:
            return 0.5
        elif self.isolation_km >= 5:
            return 0.3
        else:
            return 0.1
    
    @property
    def emission_factor(self) -> float:
        """Estimated emission factor (kg CH4/animal unit/year)"""
        # Based on EPA emission factors
        factors = {
            'dairy': 120.0,  # Dairy cows produce most methane
            'beef': 55.0,     # Beef cattle moderate
            'swine': 10.0,    # Swine lower emissions
            'poultry': 0.08,  # Poultry very low per bird
            'mixed': 40.0     # Average for mixed operations
        }
        return factors.get(self.type, 20.0)
    
    @property
    def estimated_annual_emissions_kg(self) -> float:
        """Rough estimate of annual CH4 emissions in kg"""
        return self.animal_units * self.emission_factor
    
    @property
    def estimated_hourly_emissions_kg(self) -> float:
        """Rough estimate of hourly CH4 emissions in kg"""
        return self.estimated_annual_emissions_kg / 8760  # hours in year


class ChesapeakeCAFODatabase:
    """Manages CAFO facility database for Chesapeake region"""
    
    def __init__(self, csv_path: str = "data/cafos_chesapeake.csv"):
        self.csv_path = Path(csv_path)
        self.facilities = self.load_facilities()
        self.isolation_scores = self.calculate_all_isolation_scores()
        
    def load_facilities(self) -> List[CAFOFacility]:
        """Load facilities from CSV"""
        if not self.csv_path.exists():
            logger.error(f"CAFO database not found at {self.csv_path}")
            return []
        
        df = pd.read_csv(self.csv_path)
        facilities = []
        
        for _, row in df.iterrows():
            facility = CAFOFacility(
                facility_id=row['facility_id'],
                name=row['name'],
                lat=row['lat'],
                lon=row['lon'],
                state=row['state'],
                county=row['county'],
                type=row['type'],
                animal_units=int(row['animal_units']),
                company=row['company'],
                isolation_km=float(row['isolation_km']),
                notes=row.get('notes', '')
            )
            facilities.append(facility)
        
        logger.info(f"Loaded {len(facilities)} facilities from {self.csv_path}")
        return facilities
    
    def calculate_all_isolation_scores(self) -> Dict[str, float]:
        """Calculate isolation scores for all facilities"""
        scores = {}
        for facility in self.facilities:
            scores[facility.facility_id] = facility.isolation_score
        return scores
    
    def get_isolated_facilities(self, min_isolation_km: float = 10.0) -> List[CAFOFacility]:
        """Get facilities that are isolated enough for attribution"""
        isolated = [f for f in self.facilities if f.isolation_km >= min_isolation_km]
        logger.info(f"Found {len(isolated)} isolated facilities (>{min_isolation_km}km)")
        return isolated
    
    def get_facilities_by_type(self, facility_type: str) -> List[CAFOFacility]:
        """Get all facilities of a specific type"""
        return [f for f in self.facilities if f.type == facility_type]
    
    def get_facilities_by_state(self, state: str) -> List[CAFOFacility]:
        """Get all facilities in a specific state"""
        return [f for f in self.facilities if f.state == state]
    
    def get_facility_by_id(self, facility_id: str) -> Optional[CAFOFacility]:
        """Get a specific facility by ID"""
        for facility in self.facilities:
            if facility.facility_id == facility_id:
                return facility
        return None
    
    def get_nearby_facilities(self, lat: float, lon: float, radius_km: float) -> List[CAFOFacility]:
        """Get facilities within radius of a point"""
        nearby = []
        for facility in self.facilities:
            distance = self.haversine_distance(lat, lon, facility.lat, facility.lon)
            if distance <= radius_km:
                nearby.append(facility)
        return nearby
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def get_regional_statistics(self) -> Dict:
        """Get summary statistics for the region"""
        df = pd.DataFrame([{
            'facility_id': f.facility_id,
            'type': f.type,
            'state': f.state,
            'animal_units': f.animal_units,
            'isolation_km': f.isolation_km,
            'isolation_score': f.isolation_score,
            'estimated_emissions_kg_hr': f.estimated_hourly_emissions_kg
        } for f in self.facilities])
        
        stats = {
            'total_facilities': len(self.facilities),
            'isolated_facilities': len(self.get_isolated_facilities()),
            'by_type': df.groupby('type').size().to_dict(),
            'by_state': df.groupby('state').size().to_dict(),
            'total_animal_units': df['animal_units'].sum(),
            'avg_isolation_km': df['isolation_km'].mean(),
            'total_estimated_emissions_kg_hr': df['estimated_emissions_kg_hr'].sum(),
            'top_emitters': df.nlargest(5, 'estimated_emissions_kg_hr')[
                ['facility_id', 'estimated_emissions_kg_hr']
            ].to_dict('records')
        }
        
        return stats
    
    def export_for_gee(self) -> str:
        """Export facility locations as GEE-compatible JavaScript"""
        js_code = "// CAFO Facility Locations for Chesapeake Bay\n"
        js_code += "var cafoLocations = ee.FeatureCollection([\n"
        
        for facility in self.facilities:
            js_code += f"  ee.Feature(ee.Geometry.Point([{facility.lon}, {facility.lat}]), {{\n"
            js_code += f"    'facility_id': '{facility.facility_id}',\n"
            js_code += f"    'name': '{facility.name}',\n"
            js_code += f"    'type': '{facility.type}',\n"
            js_code += f"    'animal_units': {facility.animal_units},\n"
            js_code += f"    'isolation_score': {facility.isolation_score:.2f}\n"
            js_code += "  }),\n"
        
        js_code = js_code.rstrip(",\n") + "\n]);\n"
        
        return js_code
    
    def save_isolation_scores(self, output_path: str = "data/isolation_scores.json"):
        """Save isolation scores to JSON file"""
        scores_data = {
            'metadata': {
                'total_facilities': len(self.facilities),
                'isolated_count': len(self.get_isolated_facilities()),
                'avg_isolation_km': np.mean([f.isolation_km for f in self.facilities])
            },
            'scores': {
                f.facility_id: {
                    'name': f.name,
                    'isolation_km': f.isolation_km,
                    'isolation_score': f.isolation_score,
                    'is_isolated': f.is_isolated
                } for f in self.facilities
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(scores_data, f, indent=2)
        
        logger.info(f"Saved isolation scores to {output_path}")
    
    def validate_coordinates(self) -> List[str]:
        """Validate all coordinates are within Chesapeake region"""
        chesapeake_bounds = {
            'min_lat': 36.5,
            'max_lat': 40.3,
            'min_lon': -77.8,
            'max_lon': -74.5
        }
        
        invalid = []
        for facility in self.facilities:
            if not (chesapeake_bounds['min_lat'] <= facility.lat <= chesapeake_bounds['max_lat'] and
                   chesapeake_bounds['min_lon'] <= facility.lon <= chesapeake_bounds['max_lon']):
                invalid.append(facility.facility_id)
                logger.warning(f"Facility {facility.facility_id} outside Chesapeake bounds")
        
        return invalid


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = ChesapeakeCAFODatabase()
    
    # Get statistics
    stats = db.get_regional_statistics()
    print("\n📊 Chesapeake CAFO Database Statistics:")
    print(f"Total facilities: {stats['total_facilities']}")
    print(f"Isolated facilities (>10km): {stats['isolated_facilities']}")
    print(f"Total estimated emissions: {stats['total_estimated_emissions_kg_hr']:.1f} kg/hr")
    print(f"\nFacilities by type: {stats['by_type']}")
    print(f"Facilities by state: {stats['by_state']}")
    
    # Get isolated facilities for attribution
    isolated = db.get_isolated_facilities(min_isolation_km=12.0)
    print(f"\n🎯 Best facilities for attribution (>12km isolation):")
    for facility in isolated[:5]:
        print(f"  {facility.facility_id}: {facility.name}")
        print(f"    Type: {facility.type}, Isolation: {facility.isolation_km}km")
        print(f"    Est. emissions: {facility.estimated_hourly_emissions_kg:.1f} kg/hr")
    
    # Save isolation scores
    db.save_isolation_scores()
    
    # Export for GEE
    gee_code = db.export_for_gee()
    with open("scripts/cafo_locations.js", "w") as f:
        f.write(gee_code)
    print("\n✅ Exported facility locations for Google Earth Engine")