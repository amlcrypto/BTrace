"""Bot data models"""
from typing import Optional

from pydantic import BaseModel


class CallbackDataModel(BaseModel):
    """Schema of callback data"""
    action: str
    id: int
    data: Optional[dict]
