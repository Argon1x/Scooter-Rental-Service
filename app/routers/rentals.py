from typing import List
from fastapi import APIRouter, Depends
from app.dependencies import get_service
from app.schemas import RentalResponse
from app.service import RentalService

router = APIRouter()


@router.get("", response_model=List[RentalResponse])
def get_rentals(service: RentalService = Depends(get_service)):
    rentals = service.list_rentals()
    return [r.to_dict() for r in rentals]
