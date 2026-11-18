from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    username:str = Field(min_length=3, max_length=50)
    full_name: str | None = None
    
class UserCreate(UserBase):
    password:str = Field(min_length=8, max_length=128)

class UserUpdate(BaseModel):
    email:EmailStr | None = None
    username:str | None = Field(default=None, min_length=3, max_length=50)
    full_name:str | None = None
    password:str | None = Field(default=None, min_length=8, max_length=128)

class Userout(UserBase):
    id:int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
