from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    user_type: str = Field(default="regular")


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    user_type: Optional[str] = Field(default=None)


class UserResponse(BaseModel):
    id: int
    name: str
    user_type: str
    max_rentals: int
    rented_scooter_ids: List[int]


class ScooterCreateRequest(BaseModel):
    model: str = Field(..., min_length=1)
    charge_level: int = Field(default=100, ge=0, le=100)


class ScooterUpdateRequest(BaseModel):
    model: Optional[str] = Field(default=None, min_length=1)
    charge_level: Optional[int] = Field(default=None, ge=0, le=100)


class ScooterResponse(BaseModel):
    id: int
    model: str
    charge_level: int
    status: str
    current_user_id: Optional[int] = None


class RentRequest(BaseModel):
    user_id: int = Field(..., gt=0)


class ReturnRequest(BaseModel):
    battery_used: int = Field(default=10, ge=0)


class ChargeRequest(BaseModel):
    amount: int = Field(default=50, gt=0)


class OperationResponse(BaseModel):
    message: str
    scooter: ScooterResponse


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    status: int
