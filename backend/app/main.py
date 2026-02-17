import os

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .models import load_sensors_data, load_metrics_data, load_sensor_types_data
from .schemas import SensorResponse
from natsort import natsorted, natsort_keygen

app = FastAPI(
    title="Sensor Data API",
    description="API for sensor data with sorting and filtering",
)

# CORS configuration — read trusted origins from ALLOWED_ORIGINS (comma separated).
# - Dev default: http://localhost:5173
# - In production set ALLOWED_ORIGINS="https://app.example.com,https://admin.example.com"
_allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").strip()

if _allowed == "*":
    cors_origins = ["*"]   # WARNING: do NOT use "*" in production unless intentional
else:
    cors_origins = [o.strip() for o in _allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def filter_by_type(sensor_list, filter_type):
    # Filter sensors by type, if specified
    if filter_type:
        return [s for s in sensor_list if s['type'] == filter_type]
    return sensor_list

def search_by_name(sensor_list, search):
    # Exact search by sensor name (case-insensitive)
    if search:
        search_lower = search.lower()
        return [s for s in sensor_list if search_lower in (s.get('sensor_name') or '').lower()]
    return sensor_list

def filter_by_metrics(sensor_list, metrics):
    """
    Return a NEW list of sensors where each sensor has 'measurements'
    filtered according to `metrics`. Do NOT mutate objects from the
    original `sensor_list` (avoid in‑place changes).
    """
    if not metrics:
        return sensor_list

    requested = [m.strip().lower() for m in metrics.split(",") if m.strip()]

    def keep_measurement(key: str) -> bool:
        kl = key.lower()
        for r in requested:
            if r in kl:
                return True
        return False

    new_list = []
    for s in sensor_list:
        # GUARD: sensor may not have measurements or it may not be a dict
        measurements = s.get('measurements') if isinstance(s.get('measurements'), dict) else {}

        # filtered measurements for this sensor
        filtered = {k: v for k, v in measurements.items() if keep_measurement(k)}

        # create a shallow copy of sensor and replace 'measurements' with filtered dict
        new_sensor = {**s, 'measurements': filtered}

        new_list.append(new_sensor)

    return new_list

def sort_sensors(sensor_list, sort_by, sort_order):
    # Sort sensors by the selected column and direction
    reverse = sort_order == "desc"
    if sort_by == 'sensor_name':
        nkey = natsort_keygen()
        return natsorted(sensor_list, key=lambda x: nkey(x.get('sensor_name', '')), reverse=reverse)
    elif sort_by == 'type':
        def type_sort_key(x):
            t = x.get('type', '')
            if reverse:
                t = ''.join(chr(255 - ord(c)) for c in t)
            return (t == 'n/a', t)
        return sorted(sensor_list, key=type_sort_key, reverse=False)
    elif sort_by == 'id':
        return sorted(sensor_list, key=lambda x: x.get('id', 0), reverse=reverse)
    else:
        def get_sort_value(x):
            try:
                v = x['measurements'].get(sort_by)
                if v is not None:
                    return v
                return float('inf') if not reverse else float('-inf')
            except Exception:
                return float('inf') if not reverse else float('-inf')
        return sorted(sensor_list, key=get_sort_value, reverse=reverse)

@app.get("/api/sensors", response_model=List[SensorResponse])
def get_sensors(
    sort_by: Optional[str] = Query("sensor_name", description="Column to sort by"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    filter_type: Optional[str] = Query(None, description="Filter by sensor type name"),
    search: Optional[str] = Query(None, description="Search by sensor name (case-insensitive)"),
    metrics: Optional[str] = Query(None, description="Comma-separated list of metric names (or partial names) to INCLUDE")
):
    """Return list of sensors with measurements, sorted and filtered."""
    try:
        sensors = load_sensors_data()
        metrics_list = load_metrics_data()
        sensor_types = load_sensor_types_data()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    metrics_dict = {str(m['id']): {'name': m['name'], 'units': m['units']} for m in metrics_list}
    
    sensor_list = []
    for sensor in sensors:
        sensor_data = {
            'id': sensor['id'],
            'sensor_name': sensor.get('name') or f"id{sensor['id']}",
            'type': next(
                (st['name'] for st in sensor_types 
                 if st['type'] == sensor.get('type') and st['version'] == sensor.get('variant', sensor.get('version'))),
                'n/a'
            ),
            'measurements': {}
        }
        for metric_id, metric_data in sensor.get('metrics', {}).items():
            if metric_id in metrics_dict:
                metric = metrics_dict[metric_id]
                unit = next((u['name'] for u in metric['units'] if u.get('selected')), '')
                name_with_unit = f"{metric['name']} ({unit})"
                try:
                    val = float(metric_data.get('v')) if metric_data.get('v') is not None else None
                except (ValueError, TypeError):
                    val = None
                sensor_data['measurements'][name_with_unit] = val
        sensor_list.append(sensor_data)
    
    # Apply filters and sorting
    sensor_list = filter_by_type(sensor_list, filter_type)
    sensor_list = search_by_name(sensor_list, search)
    sensor_list = filter_by_metrics(sensor_list, metrics)
    sensor_list = sort_sensors(sensor_list, sort_by, sort_order)
    return sensor_list

@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint. Provides basic API info and documentation links.
    """
    return {
        "message": "Welcome to the Sensor Data API! See /docs for interactive documentation or /api/sensors for sensor data."
    }
