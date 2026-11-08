from app.repository import InMemoryRepository
from app.service import RentalService

_repository = InMemoryRepository()
_service = RentalService(repository=_repository)
_service.seed_initial_data()


def get_repository() -> InMemoryRepository:
    return _repository


def get_service() -> RentalService:
    return _service
