from pydantic import BaseModel
from typing import Dict

class SensorResponse(BaseModel):
    """Schema for sensor response in API."""
    id: int
    sensor_name: str
    type: str
    measurements: Dict[str, float]

    class Config:
        allow_population_by_field_name = True