"""
NeuralGCM Integration for CAFO Methane Dispersion Modeling
Tracks methane plume dispersion from factory farms using Google's NeuralGCM
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple, Dict
import ee
from datetime import datetime, timedelta
import xarray as xr
import matplotlib.pyplot as plt
import folium
from folium import plugins
import json

@dataclass
class CAFOSource:
    """Represents a CAFO emission source"""
    name: str
    lat: float
    lon: float
    emission_rate_kg_hr: float  # Methane emission rate
    source_type: str  # 'dairy', 'beef', 'poultry', 'swine'
    
class MethanePlumeTracker:
    """
    Integrates satellite observations with NeuralGCM for plume tracking
    """
    
    def __init__(self, region_bounds: List[float]):
        """
        Initialize tracker with geographic bounds
        region_bounds: [west, south, east, north]
        """
        self.region = region_bounds
        self.sources = []
        
    def add_cafo_source(self, source: CAFOSource):
        """Add a CAFO emission source"""
        self.sources.append(source)
        
    def get_sentinel5p_baseline(self, date: datetime) -> xr.Dataset:
        """
        Fetch Sentinel-5P methane data for baseline
        """
        # Initialize Earth Engine
        ee.Initialize()
        
        # Define region
        region = ee.Geometry.Rectangle(self.region)
        
        # Get Sentinel-5P data
        collection = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_CH4') \
            .filterDate(date - timedelta(days=7), date) \
            .filterBounds(region)
        
        # Calculate weekly mean
        ch4_mean = collection.select('CH4_column_volume_mixing_ratio_dry_air_bias_corrected').mean()
        
        # Convert to xarray for NeuralGCM compatibility
        # This would need ee.batch.Export in practice
        return self._ee_to_xarray(ch4_mean, region)
    
    def _ee_to_xarray(self, image, region):
        """Convert Earth Engine image to xarray (placeholder)"""
        # In practice, export to Cloud Storage then load
        # For now, create synthetic data
        lons = np.linspace(self.region[0], self.region[2], 50)
        lats = np.linspace(self.region[1], self.region[3], 50)
        
        # Synthetic baseline ~1850 ppb
        data = np.random.normal(1850, 20, (len(lats), len(lons)))
        
        return xr.Dataset({
            'ch4_ppb': (['lat', 'lon'], data)
        }, coords={'lon': lons, 'lat': lats})
    
    def prepare_neuralgcm_forcing(self, sources: List[CAFOSource], 
                                  met_data: Dict) -> xr.Dataset:
        """
        Prepare emission sources as NeuralGCM forcing terms
        """
        # Create emission field
        lons = np.linspace(self.region[0], self.region[2], 100)
        lats = np.linspace(self.region[1], self.region[3], 100)
        
        emissions = np.zeros((len(lats), len(lons)))
        
        for source in sources:
            # Find nearest grid cell
            lon_idx = np.argmin(np.abs(lons - source.lon))
            lat_idx = np.argmin(np.abs(lats - source.lat))
            
            # Add point source (kg/hr -> kg/m2/s for grid cell)
            grid_area_m2 = 111000 * 111000 * 0.01  # ~1km2 at equator
            emissions[lat_idx, lon_idx] = source.emission_rate_kg_hr / 3600 / grid_area_m2
        
        # Add meteorology (from GraphCast or ERA5)
        forcing = xr.Dataset({
            'ch4_emissions': (['time', 'lat', 'lon'], emissions[np.newaxis, :, :]),
            'u_wind': (['time', 'lat', 'lon'], met_data.get('u_wind', np.zeros_like(emissions))[np.newaxis, :, :]),
            'v_wind': (['time', 'lat', 'lon'], met_data.get('v_wind', np.zeros_like(emissions))[np.newaxis, :, :]),
            'temperature': (['time', 'lat', 'lon'], met_data.get('temp', 
                          np.full_like(emissions, 288))[np.newaxis, :, :])
        }, coords={
            'time': pd.date_range(datetime.now(), periods=1),
            'lat': lats,
            'lon': lons
        })
        
        return forcing
    
    def run_dispersion_model(self, forcing: xr.Dataset, 
                           hours: int = 72) -> xr.Dataset:
        """
        Run simplified dispersion model (placeholder for NeuralGCM)
        In production, this would call actual NeuralGCM
        """
        # Simplified Gaussian plume model as placeholder
        timesteps = hours
        dt = 3600  # 1 hour timesteps
        
        # Initialize concentration field
        shape = (timesteps, len(forcing.lat), len(forcing.lon))
        ch4_conc = np.zeros(shape)
        
        # Get wind fields
        u_wind = forcing.u_wind.values[0]
        v_wind = forcing.v_wind.values[0]
        emissions = forcing.ch4_emissions.values[0]
        
        # Simple advection-diffusion
        for t in range(timesteps):
            if t == 0:
                ch4_conc[t] = emissions * dt
            else:
                # Advection (upwind scheme)
                ch4_conc[t] = ch4_conc[t-1].copy()
                
                # Add new emissions
                ch4_conc[t] += emissions * dt
                
                # Simple diffusion
                diff_coeff = 100  # m2/s
                ch4_conc[t] += diff_coeff * dt * np.gradient(np.gradient(ch4_conc[t]))[0]
                
                # Wind transport (simplified)
                if np.mean(np.abs(u_wind)) > 0:
                    ch4_conc[t] = np.roll(ch4_conc[t], int(u_wind.mean() * dt / 1000), axis=1)
                if np.mean(np.abs(v_wind)) > 0:
                    ch4_conc[t] = np.roll(ch4_conc[t], int(v_wind.mean() * dt / 1000), axis=0)
        
        times = pd.date_range(datetime.now(), periods=timesteps, freq='h')
        
        return xr.Dataset({
            'ch4_concentration': (['time', 'lat', 'lon'], ch4_conc),
            'exposure_ppb': (['lat', 'lon'], np.mean(ch4_conc, axis=0) * 1e9)  # Convert to ppb
        }, coords={
            'time': times,
            'lat': forcing.lat,
            'lon': forcing.lon
        })
    
    def calculate_health_impact_zones(self, dispersion: xr.Dataset) -> Dict:
        """
        Calculate population exposure and health impacts
        """
        exposure = dispersion.exposure_ppb.values
        
        # Define exposure thresholds (ppb above baseline)
        thresholds = {
            'high_risk': 100,  # >100 ppb above baseline
            'moderate_risk': 50,  # 50-100 ppb
            'low_risk': 20  # 20-50 ppb
        }
        
        zones = {}
        for level, threshold in thresholds.items():
            mask = exposure > threshold
            if np.any(mask):
                affected_coords = []
                lats, lons = np.where(mask)
                for lat_idx, lon_idx in zip(lats, lons):
                    affected_coords.append({
                        'lat': float(dispersion.lat[lat_idx]),
                        'lon': float(dispersion.lon[lon_idx]),
                        'exposure_ppb': float(exposure[lat_idx, lon_idx])
                    })
                zones[level] = affected_coords
        
        return zones
    
    def generate_alert_map(self, dispersion: xr.Dataset, 
                          output_path: str = 'outputs/dispersion_map.html'):
        """
        Create interactive Folium map with dispersion plumes
        """
        # Center map on region
        center_lat = np.mean([self.region[1], self.region[3]])
        center_lon = np.mean([self.region[0], self.region[2]])
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
        
        # Add CAFO markers
        for source in self.sources:
            folium.Marker(
                [source.lat, source.lon],
                popup=f"{source.name}<br>Type: {source.source_type}<br>"
                      f"Emissions: {source.emission_rate_kg_hr:.1f} kg/hr",
                icon=folium.Icon(color='red', icon='warning')
            ).add_to(m)
        
        # Add concentration heatmap
        exposure = dispersion.exposure_ppb.values
        heat_data = []
        
        for i, lat in enumerate(dispersion.lat.values):
            for j, lon in enumerate(dispersion.lon.values):
                if exposure[i, j] > 20:  # Only show elevated concentrations
                    heat_data.append([float(lat), float(lon), 
                                    float(exposure[i, j])])
        
        if heat_data:
            plugins.HeatMap(heat_data, radius=15, blur=25).add_to(m)
        
        # Add exposure zones
        zones = self.calculate_health_impact_zones(dispersion)
        
        colors = {'high_risk': 'red', 'moderate_risk': 'orange', 'low_risk': 'yellow'}
        
        for level, coords in zones.items():
            for point in coords[:100]:  # Limit points for performance
                folium.CircleMarker(
                    [point['lat'], point['lon']],
                    radius=5,
                    color=colors[level],
                    fill=True,
                    fillOpacity=0.3,
                    popup=f"{level.replace('_', ' ').title()}<br>"
                          f"Exposure: {point['exposure_ppb']:.1f} ppb"
                ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px">
        <p style="margin: 0;"><b>Methane Exposure Levels</b></p>
        <p style="margin: 5px;"><span style="color: red;">●</span> High Risk (>100 ppb)</p>
        <p style="margin: 5px;"><span style="color: orange;">●</span> Moderate (50-100 ppb)</p>
        <p style="margin: 5px;"><span style="color: gold;">●</span> Low (20-50 ppb)</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        m.save(output_path)
        return m
    
    def generate_community_alerts(self, zones: Dict) -> List[Dict]:
        """
        Generate alert messages for affected communities
        """
        alerts = []
        
        for level, coords in zones.items():
            if coords:
                alert = {
                    'severity': level,
                    'affected_area_km2': len(coords) * 1.0,  # Rough estimate
                    'max_exposure_ppb': max(p['exposure_ppb'] for p in coords),
                    'coordinates': coords[:10],  # First 10 points
                    'message': self._create_alert_message(level, len(coords))
                }
                alerts.append(alert)
        
        return alerts
    
    def _create_alert_message(self, risk_level: str, num_points: int) -> str:
        """Create human-readable alert message"""
        messages = {
            'high_risk': f"⚠️ HIGH METHANE EXPOSURE: {num_points} areas detected with "
                        "methane levels >100 ppb above baseline. Vulnerable populations "
                        "should limit outdoor activities.",
            'moderate_risk': f"🟡 MODERATE EXPOSURE: {num_points} areas with elevated "
                           "methane (50-100 ppb above normal). Monitor air quality.",
            'low_risk': f"🟢 LOW EXPOSURE: {num_points} areas with slightly elevated "
                       "methane levels. No immediate health concern."
        }
        return messages.get(risk_level, "Unknown risk level")


def main():
    """
    Example workflow for Chesapeake Bay CAFOs
    """
    # Initialize tracker for Chesapeake region
    chesapeake_bounds = [-77.8, 36.5, -74.5, 40.3]
    tracker = MethanePlumeTracker(chesapeake_bounds)
    
    # Add example CAFOs (in practice, load from CSV)
    cafos = [
        CAFOSource("Delmarva Dairy #1", 38.5, -75.8, 50.0, "dairy"),
        CAFOSource("Eastern Shore Poultry", 38.2, -76.1, 30.0, "poultry"),
        CAFOSource("Sussex Beef Operations", 38.7, -75.5, 45.0, "beef"),
    ]
    
    for cafo in cafos:
        tracker.add_cafo_source(cafo)
    
    # Get baseline methane
    baseline = tracker.get_sentinel5p_baseline(datetime.now())
    print(f"Baseline CH4: {baseline.ch4_ppb.mean().values:.1f} ppb")
    
    # Prepare forcing with synthetic wind data
    met_data = {
        'u_wind': np.ones((50, 50)) * 5,  # 5 m/s eastward
        'v_wind': np.ones((50, 50)) * 2,  # 2 m/s northward
        'temp': np.full((50, 50), 288)  # 15°C
    }
    
    forcing = tracker.prepare_neuralgcm_forcing(cafos, met_data)
    
    # Run dispersion model
    print("Running dispersion model...")
    dispersion = tracker.run_dispersion_model(forcing, hours=72)
    
    # Calculate health impacts
    zones = tracker.calculate_health_impact_zones(dispersion)
    print(f"\nHealth Impact Zones:")
    for level, coords in zones.items():
        print(f"  {level}: {len(coords)} grid cells affected")
    
    # Generate alerts
    alerts = tracker.generate_community_alerts(zones)
    for alert in alerts:
        print(f"\n{alert['message']}")
    
    # Create visualization
    print("\nGenerating interactive map...")
    tracker.generate_alert_map(dispersion, 'outputs/chesapeake_dispersion.html')
    print("Map saved to outputs/chesapeake_dispersion.html")
    
    # Export data for advocacy
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'cafos': [{'name': c.name, 'lat': c.lat, 'lon': c.lon, 
                  'emissions_kg_hr': c.emission_rate_kg_hr} for c in cafos],
        'affected_zones': {k: len(v) for k, v in zones.items()},
        'alerts': alerts
    }
    
    with open('outputs/dispersion_report.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print("\nReport exported to outputs/dispersion_report.json")


if __name__ == "__main__":
    main()