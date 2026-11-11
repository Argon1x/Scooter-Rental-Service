from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.dependencies import get_service
from app.schemas import (
    ChargeRequest,
    MessageResponse,
    OperationResponse,
    RentRequest,
    ReturnRequest,
    ScooterCreateRequest,
    ScooterResponse,
    ScooterUpdateRequest,
)
from app.service import RentalService

router = APIRouter()


@router.get("", response_model=List[ScooterResponse])
def get_scooters(
    status: Optional[str] = Query(default=None),
    min_charge: Optional[int] = Query(default=None),
    service: RentalService = Depends(get_service),
):
    scooters = service.list_scooters(status=status, min_charge=min_charge)
    return [s.to_dict() for s in scooters]


@router.post("", response_model=ScooterResponse, status_code=status.HTTP_201_CREATED)
def create_scooter(
    request: ScooterCreateRequest,
    service: RentalService = Depends(get_service),
):
    scooter = service.create_scooter(model=request.model, charge_level=request.charge_level)
    return scooter.to_dict()


@router.get("/{scooter_id}", response_model=ScooterResponse)
def get_scooter(
    scooter_id: int,
    service: RentalService = Depends(get_service),
):
    scooter = service.get_scooter(scooter_id)
    return scooter.to_dict()


@router.put("/{scooter_id}", response_model=ScooterResponse)
def update_scooter(
    scooter_id: int,
    request: ScooterUpdateRequest,
    service: RentalService = Depends(get_service),
):
    scooter = service.update_scooter(
        scooter_id=scooter_id,
        model=request.model,
        charge_level=request.charge_level,
    )
    return scooter.to_dict()


@router.delete("/{scooter_id}", response_model=MessageResponse)
def delete_scooter(
    scooter_id: int,
    service: RentalService = Depends(get_service),
):
    service.delete_scooter(scooter_id)
    return {"message": f"Самокат с ID {scooter_id} успешно удален."}


@router.post("/{scooter_id}/rent", response_model=OperationResponse)
def rent_scooter(
    scooter_id: int,
    request: RentRequest,
    service: RentalService = Depends(get_service),
):
    scooter = service.rent_scooter(scooter_id=scooter_id, user_id=request.user_id)
    return {
        "message": f"Самокат №{scooter_id} успешно выдан пользователю №{request.user_id}.",
        "scooter": scooter.to_dict(),
    }


@router.post("/{scooter_id}/return", response_model=OperationResponse)
def return_scooter(
    scooter_id: int,
    request: ReturnRequest,
    service: RentalService = Depends(get_service),
):
    scooter = service.return_scooter(scooter_id=scooter_id, battery_used=request.battery_used)
    return {
        "message": f"Поездка на самокате №{scooter_id} успешно завершена.",
        "scooter": scooter.to_dict(),
    }


@router.post("/{scooter_id}/charge", response_model=OperationResponse)
def charge_scooter(
    scooter_id: int,
    request: ChargeRequest,
    service: RentalService = Depends(get_service),
):
    scooter = service.charge_scooter(scooter_id=scooter_id, amount=request.amount)
    return {
        "message": f"Самокат №{scooter_id} успешно заряжен.",
        "scooter": scooter.to_dict(),
    }
