from enum import Enum
from typing import Any, Dict, List, Optional
from app.exceptions import ValidationError


class ScooterStatus(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"


class User:
    user_type: str = "base"
    max_rentals: int = 1

    def __init__(self, user_id: int, name: str):
        self.id = user_id
        self.name = name
        self.rented_scooter_ids: List[int] = []

    def can_rent(self) -> bool:
        return len(self.rented_scooter_ids) < self.max_rentals

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "user_type": self.user_type,
            "max_rentals": self.max_rentals,
            "rented_scooter_ids": list(self.rented_scooter_ids),
        }


class RegularUser(User):
    user_type = "regular"
    max_rentals = 1


class VipUser(User):
    user_type = "vip"
    max_rentals = 3


def create_user_instance(user_id: int, name: str, user_type: str) -> User:
    if not isinstance(user_type, str):
        raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")
    clean_type = user_type.strip().lower()
    if clean_type == "regular":
        return RegularUser(user_id=user_id, name=name)
    elif clean_type == "vip":
        return VipUser(user_id=user_id, name=name)
    else:
        raise ValidationError(
            f"Неизвестный тип пользователя '{user_type}'. Допустимые типы: 'regular', 'vip'."
        )


class Scooter:
    def __init__(self, scooter_id: int, model: str, charge_level: int = 100):
        self.id = scooter_id
        self.model = model
        self.charge_level = charge_level
        self.status = ScooterStatus.AVAILABLE if charge_level >= 20 else ScooterStatus.MAINTENANCE
        self.current_user_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model": self.model,
            "charge_level": self.charge_level,
            "status": self.status.value,
            "current_user_id": self.current_user_id,
        }
