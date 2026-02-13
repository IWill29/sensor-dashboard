from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from models import load_sensors_data, load_metrics_data, load_sensor_types_data
from schemas import SensorResponse

app = FastAPI(
    title="Sensor Data API",
    description="API for sensor data with sorting and filtering",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/sensors", response_model=List[SensorResponse])
def get_sensors(
    sort_by: Optional[str] = Query("sensor_name", description="Column to sort by"),
    sort_order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    filter_type: Optional[str] = Query(None, description="Filter by sensor type")
):
    """Return list of sensors with measurements, sorted and filtered."""
    try:
        sensors = load_sensors_data()
        metrics = load_metrics_data()
        sensor_types = load_sensor_types_data()
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    metrics_dict = {str(m['id']): {'name': m['name'], 'units': m['units']} for m in metrics}
    
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
                sensor_data['measurements'][name_with_unit] = metric_data['v']
        
        sensor_list.append(sensor_data)
    
    if filter_type:
        sensor_list = [s for s in sensor_list if s['type'] == filter_type]
    
    reverse = sort_order == "desc"
    if sort_by in ['sensor_name', 'type']:
        sensor_list.sort(key=lambda x: x[sort_by], reverse=reverse)
    elif sort_by in ['id']:
        sensor_list.sort(key=lambda x: x[sort_by], reverse=reverse)
    else:
        sensor_list.sort(key=lambda x: x['measurements'].get(sort_by, 0), reverse=reverse)
    
    return sensor_list