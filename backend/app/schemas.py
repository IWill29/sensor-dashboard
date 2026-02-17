from pydantic import BaseModel
from typing import Dict, Optional

class SensorResponse(BaseModel):
    """Schema for sensor response in API."""
    id: int
    sensor_name: str
    type: str
    measurements: Dict[str, Optional[float]]

    class Config:
        allow_population_by_field_name = True
