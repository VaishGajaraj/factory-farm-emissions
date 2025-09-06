"""
FastAPI server for Factory Farm Emissions Tracker
Provides REST API for dispersion modeling and data access
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import json
import uuid
from neuralgcm_integration import MethanePlumeTracker, CAFOSource
import pandas as pd
import numpy as np
import redis
import os

app = FastAPI(
    title="Factory Farm Emissions API",
    description="Real-time methane monitoring and dispersion modeling for CAFOs",
    version="1.0.0"
)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis for caching (optional)
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    print("Redis not available, using in-memory cache")

# In-memory cache fallback
cache = {}

# Request/Response Models
class CAFOInput(BaseModel):
    name: str
    lat: float
    lon: float
    emission_rate_kg_hr: float
    source_type: str

class DispersionRequest(BaseModel):
    cafos: List[CAFOInput]
    wind_speed: float = 5.0
    wind_direction: float = 2.0
    temperature: float = 288.0
    forecast_hours: int = 72
    region_bounds: List[float] = [-77.8, 36.5, -74.5, 40.3]

class AlertSubscription(BaseModel):
    email: str
    lat: float
    lon: float
    threshold_ppb: float = 50.0
    
class EmissionReport(BaseModel):
    facility_name: str
    date_range: List[str]
    include_dispersion: bool = False
    include_health_impacts: bool = True

# Background task queue
task_queue = {}

def cache_set(key: str, value: dict, expire: int = 3600):
    """Set cache value with expiration"""
    if REDIS_AVAILABLE:
        redis_client.setex(key, expire, json.dumps(value))
    else:
        cache[key] = {'value': value, 'expire': datetime.now() + timedelta(seconds=expire)}

def cache_get(key: str) -> Optional[dict]:
    """Get cache value"""
    if REDIS_AVAILABLE:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    else:
        if key in cache:
            if cache[key]['expire'] > datetime.now():
                return cache[key]['value']
            else:
                del cache[key]
        return None

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Factory Farm Emissions Tracker API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "cafos": "/api/cafos",
            "dispersion": "/api/dispersion",
            "alerts": "/api/alerts",
            "reports": "/api/reports"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis": REDIS_AVAILABLE
    }

@app.get("/api/cafos")
async def get_cafos(
    region: Optional[str] = "chesapeake",
    type_filter: Optional[str] = None,
    limit: int = 100
):
    """Get CAFO registry data"""
    
    # Check cache
    cache_key = f"cafos:{region}:{type_filter}:{limit}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Simulated database query
    cafos = [
        {
            "id": f"cafo_{i}",
            "name": f"Farm #{i}",
            "lat": 38.5 + np.random.uniform(-2, 2),
            "lon": -75.8 + np.random.uniform(-2, 2),
            "type": np.random.choice(["dairy", "beef", "poultry", "swine"]),
            "emissions_kg_hr": np.random.uniform(20, 80),
            "animals": np.random.randint(500, 5000),
            "permit_status": np.random.choice(["Active", "Expired", "Under Review"]),
            "last_inspection": (datetime.now() - timedelta(days=np.random.randint(30, 365))).isoformat()
        }
        for i in range(min(limit, 100))
    ]
    
    if type_filter:
        cafos = [c for c in cafos if c["type"] == type_filter]
    
    result = {
        "region": region,
        "count": len(cafos),
        "cafos": cafos,
        "timestamp": datetime.now().isoformat()
    }
    
    cache_set(cache_key, result, expire=3600)
    return result

@app.post("/api/dispersion")
async def run_dispersion(request: DispersionRequest, background_tasks: BackgroundTasks):
    """Run dispersion model for specified CAFOs"""
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Quick validation
    if not request.cafos:
        raise HTTPException(status_code=400, detail="No CAFOs provided")
    
    # Check if similar request was recently processed
    cache_key = f"dispersion:{hash(str(request.dict()))}"
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    # Initialize task
    task_queue[task_id] = {
        "status": "pending",
        "started": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    # Run dispersion model in background
    background_tasks.add_task(run_dispersion_task, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Dispersion model queued for processing",
        "check_status": f"/api/tasks/{task_id}"
    }

async def run_dispersion_task(task_id: str, request: DispersionRequest):
    """Background task to run dispersion model"""
    
    try:
        task_queue[task_id]["status"] = "running"
        
        # Initialize tracker
        tracker = MethanePlumeTracker(request.region_bounds)
        
        # Add CAFOs
        for cafo in request.cafos:
            source = CAFOSource(
                name=cafo.name,
                lat=cafo.lat,
                lon=cafo.lon,
                emission_rate_kg_hr=cafo.emission_rate_kg_hr,
                source_type=cafo.source_type
            )
            tracker.add_cafo_source(source)
        
        # Prepare meteorological data
        grid_size = 50
        met_data = {
            'u_wind': np.ones((grid_size, grid_size)) * request.wind_speed,
            'v_wind': np.ones((grid_size, grid_size)) * request.wind_direction,
            'temp': np.full((grid_size, grid_size), request.temperature)
        }
        
        # Run model
        forcing = tracker.prepare_neuralgcm_forcing(tracker.sources, met_data)
        dispersion = tracker.run_dispersion_model(forcing, hours=request.forecast_hours)
        zones = tracker.calculate_health_impact_zones(dispersion)
        alerts = tracker.generate_community_alerts(zones)
        
        # Prepare results
        result = {
            "task_id": task_id,
            "status": "completed",
            "completed": datetime.now().isoformat(),
            "summary": {
                "cafos_modeled": len(request.cafos),
                "forecast_hours": request.forecast_hours,
                "max_exposure_ppb": float(dispersion.exposure_ppb.max()),
                "mean_exposure_ppb": float(dispersion.exposure_ppb.mean()),
            },
            "impact_zones": {
                "high_risk": len(zones.get("high_risk", [])),
                "moderate_risk": len(zones.get("moderate_risk", [])),
                "low_risk": len(zones.get("low_risk", []))
            },
            "alerts": alerts,
            "dispersion_grid": {
                "lat_min": float(dispersion.lat.min()),
                "lat_max": float(dispersion.lat.max()),
                "lon_min": float(dispersion.lon.min()),
                "lon_max": float(dispersion.lon.max()),
                "resolution_km": 1.0
            }
        }
        
        task_queue[task_id] = result
        
        # Cache result
        cache_key = f"dispersion:{hash(str(request.dict()))}"
        cache_set(cache_key, result, expire=7200)
        
    except Exception as e:
        task_queue[task_id] = {
            "status": "failed",
            "error": str(e),
            "completed": datetime.now().isoformat()
        }

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Check status of background task"""
    
    if task_id not in task_queue:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_queue[task_id]

@app.get("/api/emissions/timeseries")
async def get_emissions_timeseries(
    lat: float,
    lon: float,
    days: int = 30,
    satellite: str = "sentinel5p"
):
    """Get historical emissions time series for a location"""
    
    # Generate synthetic time series (in production, query actual satellite data)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    baseline = 1850
    seasonal_component = 30 * np.sin(np.arange(days) * 2 * np.pi / 365)
    noise = np.random.normal(0, 20, days)
    trend = np.linspace(0, 10, days)
    
    values = baseline + seasonal_component + noise + trend
    
    return {
        "location": {"lat": lat, "lon": lon},
        "satellite": satellite,
        "timeseries": [
            {
                "date": date.isoformat(),
                "ch4_ppb": float(value),
                "quality": np.random.uniform(0.7, 1.0)
            }
            for date, value in zip(dates, values)
        ],
        "statistics": {
            "mean": float(values.mean()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
            "trend": "increasing" if trend[-1] > trend[0] else "stable"
        }
    }

@app.post("/api/alerts/subscribe")
async def subscribe_alerts(subscription: AlertSubscription):
    """Subscribe to emission alerts for a location"""
    
    # In production, save to database
    alert_id = str(uuid.uuid4())
    
    return {
        "alert_id": alert_id,
        "status": "subscribed",
        "location": {"lat": subscription.lat, "lon": subscription.lon},
        "threshold_ppb": subscription.threshold_ppb,
        "message": "You will receive alerts when methane exceeds threshold"
    }

@app.get("/api/alerts/active")
async def get_active_alerts(region: Optional[str] = "chesapeake"):
    """Get currently active emission alerts"""
    
    # Generate sample alerts
    alerts = [
        {
            "id": str(uuid.uuid4()),
            "severity": "high",
            "location": {"lat": 38.5, "lon": -75.8},
            "facility": "Delmarva Dairy #1",
            "ch4_ppb": 1950,
            "threshold_exceeded": 100,
            "timestamp": datetime.now().isoformat(),
            "message": "High methane levels detected near residential area"
        },
        {
            "id": str(uuid.uuid4()),
            "severity": "moderate",
            "location": {"lat": 38.2, "lon": -76.1},
            "facility": "Eastern Shore Poultry",
            "ch4_ppb": 1900,
            "threshold_exceeded": 50,
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "message": "Moderate elevation in methane levels"
        }
    ]
    
    return {
        "region": region,
        "active_alerts": len(alerts),
        "alerts": alerts,
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/reports/generate")
async def generate_report(report: EmissionReport):
    """Generate emission report for a facility"""
    
    report_id = str(uuid.uuid4())
    
    # In production, generate actual PDF/Word report
    return {
        "report_id": report_id,
        "status": "generating",
        "facility": report.facility_name,
        "estimated_time": "2 minutes",
        "download_url": f"/api/reports/{report_id}/download"
    }

@app.get("/api/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download generated report"""
    
    # In production, serve actual file
    return {
        "report_id": report_id,
        "status": "ready",
        "formats": {
            "pdf": f"/files/reports/{report_id}.pdf",
            "word": f"/files/reports/{report_id}.docx",
            "csv": f"/files/reports/{report_id}_data.csv"
        }
    }

@app.get("/api/statistics")
async def get_statistics(region: Optional[str] = "chesapeake"):
    """Get regional emission statistics"""
    
    return {
        "region": region,
        "statistics": {
            "total_cafos": 127,
            "monitored_cafos": 89,
            "total_emissions_kg_day": 45600,
            "population_exposed": 12450,
            "avg_ch4_ppb": 1865,
            "violations_ytd": 23,
            "alerts_last_30d": 47
        },
        "trends": {
            "emissions": "increasing",
            "violations": "stable",
            "monitoring_coverage": "improving"
        },
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/validation/compare")
async def compare_with_ground_truth(
    facility_id: str,
    date: Optional[str] = None
):
    """Compare satellite observations with ground measurements"""
    
    # Simulated validation data
    return {
        "facility_id": facility_id,
        "date": date or datetime.now().date().isoformat(),
        "satellite_measurement": {
            "ch4_ppb": 1875,
            "uncertainty": 25,
            "source": "Sentinel-5P"
        },
        "ground_measurement": {
            "ch4_ppb": 1890,
            "uncertainty": 10,
            "source": "EPA Monitor Station #42"
        },
        "validation": {
            "difference_ppb": 15,
            "within_uncertainty": True,
            "correlation": 0.89,
            "rmse": 22.5
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)