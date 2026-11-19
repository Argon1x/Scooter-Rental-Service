from app.database import SessionLocal
from app.repository import SqlAlchemyRepository
from app.service import RentalService

_repository = SqlAlchemyRepository(session_factory=SessionLocal)
_service = RentalService(repository=_repository)


def get_repository() -> SqlAlchemyRepository:
    return _repository


def get_service() -> RentalService:
    return _service
