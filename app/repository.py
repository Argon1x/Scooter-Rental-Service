from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, sessionmaker
from app.models import RentalModel, ScooterModel, UserModel


class SqlAlchemyRepository:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory

    @property
    def session_factory(self) -> sessionmaker:
        return self._session_factory

    def save_user(self, user: UserModel) -> UserModel:
        with self._session_factory() as session:
            with session.begin():
                session.add(user)
            session.refresh(user)
            return user

    def find_user_by_id(self, user_id: int) -> Optional[UserModel]:
        with self._session_factory() as session:
            return (
                session.query(UserModel)
                .options(joinedload(UserModel.rented_scooters))
                .filter(UserModel.id == user_id)
                .first()
            )

    def find_all_users(self) -> List[UserModel]:
        with self._session_factory() as session:
            return (
                session.query(UserModel)
                .options(joinedload(UserModel.rented_scooters))
                .all()
            )

    def delete_user_by_id(self, user_id: int) -> None:
        with self._session_factory() as session:
            with session.begin():
                user = session.query(UserModel).filter(UserModel.id == user_id).first()
                if user:
                    session.delete(user)

    def save_scooter(self, scooter: ScooterModel) -> ScooterModel:
        with self._session_factory() as session:
            with session.begin():
                session.add(scooter)
            session.refresh(scooter)
            return scooter

    def find_scooter_by_id(self, scooter_id: int) -> Optional[ScooterModel]:
        with self._session_factory() as session:
            return (
                session.query(ScooterModel)
                .options(joinedload(ScooterModel.current_user))
                .filter(ScooterModel.id == scooter_id)
                .first()
            )

    def find_all_scooters(self) -> List[ScooterModel]:
        with self._session_factory() as session:
            return (
                session.query(ScooterModel)
                .options(joinedload(ScooterModel.current_user))
                .all()
            )

    def delete_scooter_by_id(self, scooter_id: int) -> None:
        with self._session_factory() as session:
            with session.begin():
                scooter = session.query(ScooterModel).filter(ScooterModel.id == scooter_id).first()
                if scooter:
                    session.delete(scooter)

    def find_all_rentals(self) -> List[RentalModel]:
        with self._session_factory() as session:
            return (
                session.query(RentalModel)
                .options(
                    joinedload(RentalModel.user),
                    joinedload(RentalModel.scooter),
                )
                .all()
            )


InMemoryRepository = SqlAlchemyRepository
