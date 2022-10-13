"""Bot data models"""

from pydantic import BaseModel


class CallbackDataModel(BaseModel):
    action: str
    id: int
