from typing import Dict, List, Optional
from app.models import Scooter, User


class InMemoryRepository:
    def __init__(self):
        self._users: Dict[int, User] = {}
        self._scooters: Dict[int, Scooter] = {}
        self._next_user_id: int = 1
        self._next_scooter_id: int = 1

    def save_user(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def get_next_user_id(self) -> int:
        uid = self._next_user_id
        self._next_user_id += 1
        return uid

    def find_user_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def find_all_users(self) -> List[User]:
        return list(self._users.values())

    def delete_user_by_id(self, user_id: int) -> None:
        if user_id in self._users:
            del self._users[user_id]

    def save_scooter(self, scooter: Scooter) -> Scooter:
        self._scooters[scooter.id] = scooter
        return scooter

    def get_next_scooter_id(self) -> int:
        sid = self._next_scooter_id
        self._next_scooter_id += 1
        return sid

    def find_scooter_by_id(self, scooter_id: int) -> Optional[Scooter]:
        return self._scooters.get(scooter_id)

    def find_all_scooters(self) -> List[Scooter]:
        return list(self._scooters.values())

    def delete_scooter_by_id(self, scooter_id: int) -> None:
        if scooter_id in self._scooters:
            del self._scooters[scooter_id]
