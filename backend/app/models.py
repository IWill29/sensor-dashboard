import json
import os
from typing import List, Dict, Any

def load_sensors_data() -> List[Dict[str, Any]]:
    """Load sensor data from sensors.json and convert to list."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    try:
        with open(os.path.join(data_dir, 'sensors.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        sensors = []
        for id_str, sensor in data.items():
            sensor['id'] = int(id_str)
            sensors.append(sensor)
        return sensors
    except FileNotFoundError:
        raise FileNotFoundError("sensors.json file not found.")
    except json.JSONDecodeError:
        raise ValueError("sensors.json is not valid JSON.")

def load_metrics_data() -> List[Dict[str, Any]]:
    """Load metrics data from metrics.json."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    try:
        with open(os.path.join(data_dir, 'metrics.json'), 'r', encoding='utf-8') as f:
            return json.load(f)['data']['items']
    except KeyError:
        raise ValueError("metrics.json structure is invalid.")
    except (FileNotFoundError, json.JSONDecodeError):
        raise FileNotFoundError("metrics.json file not found or invalid.")

def load_sensor_types_data() -> List[Dict[str, Any]]:
    """Load sensor types data from sensorTypes.json and convert to list."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    try:
        with open(os.path.join(data_dir, 'sensorTypes.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        types = []
        for type_num, variants in data.items():
            for var_num, info in variants.items():
                types.append({
                    'type': int(type_num),
                    'version': int(var_num),
                    'name': info['name']
                })
        return types
    except (FileNotFoundError, json.JSONDecodeError):
        raise FileNotFoundError("sensorTypes.json file not found or invalid.")