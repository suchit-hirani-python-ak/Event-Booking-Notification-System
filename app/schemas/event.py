from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
from datetime import datetime
from typing import Annotated

# Helper to handle MongoDB ObjectId as a string in JSON
PyObjectId = Annotated[str, BeforeValidator(str)]

class EventRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    date: datetime # Pydantic will auto-parse "2026-04-27" to a datetime object
    location: str
    total_slots: int = Field(..., gt=0)
    available_slots: int = Field(..., ge=0) # Changed to ge=0 (slots can be 0)
    created_by: PyObjectId
    # @model_validator(mode='after')
    # def check_slots(self) -> 'EventRequest':
    #     if self.available_slots > self.total_slots:
    #         raise ValueError("available_slots cannot exceed total_slots")
    #     return self

class EventResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    title: str
    date: datetime
    location: str
    total_slots: int
    available_slots: int
    created_by: PyObjectId
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True, 
        populate_by_name=True
    )
    
class EventAllResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    title: str
    date: datetime
    location: str
    total_slots: int
    available_slots: int
