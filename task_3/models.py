from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None
    is_subscribed: Optional[bool] = None

    @validator('age')
    def age_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('age must be a positive integer')
        return v
