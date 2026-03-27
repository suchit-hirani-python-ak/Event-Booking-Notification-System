from pydantic import BaseModel, ConfigDict, Field, BeforeValidator, model_validator
from datetime import datetime
from typing import Annotated

# Helper to handle MongoDB ObjectId as a string in JSON
PyObjectId = Annotated[str, BeforeValidator(str)]

class BookingRequest(BaseModel):
    event_id: PyObjectId

class BookingResponse(BaseModel):
    id: PyObjectId=Field(alias="_id")
    user_id: PyObjectId
    event_id: PyObjectId
    status: str= "confirmed"
    created: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )