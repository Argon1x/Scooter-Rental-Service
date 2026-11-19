from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.dependencies import get_service
from app.schemas import (
    MessageResponse,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.service import RentalService

router = APIRouter()


@router.get("", response_model=List[UserResponse])
def get_users(
    type: Optional[str] = Query(default=None),
    service: RentalService = Depends(get_service),
):
    users = service.list_users(user_type=type)
    return [u.to_dict() for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreateRequest,
    service: RentalService = Depends(get_service),
):
    user = service.create_user(name=request.name, user_type=request.user_type)
    return user.to_dict()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: RentalService = Depends(get_service),
):
    user = service.get_user(user_id)
    return user.to_dict()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    service: RentalService = Depends(get_service),
):
    user = service.update_user(user_id=user_id, name=request.name, user_type=request.user_type)
    return user.to_dict()


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    service: RentalService = Depends(get_service),
):
    service.delete_user(user_id)
    return {"message": f"Пользователь с ID {user_id} успешно удален."}
