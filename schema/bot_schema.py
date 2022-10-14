"""Bot data models"""

from pydantic import BaseModel


class CallbackDataModel(BaseModel):
    """Schema of callback data"""
    action: str
    id: int
