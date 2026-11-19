from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.exceptions import ValidationError


class ScooterStatus(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"


class UserTypeMeta(type):
    def __instancecheck__(cls, instance):
        if cls.__name__ == "RegularUser":
            return isinstance(instance, UserModel) and getattr(instance, "user_type", None) == "regular"
        if cls.__name__ == "VipUser":
            return isinstance(instance, UserModel) and getattr(instance, "user_type", None) == "vip"
        return super().__instancecheck__(instance)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    user_type = Column(String, nullable=False, default="regular")

    rented_scooters = relationship(
        "ScooterModel",
        back_populates="current_user",
        foreign_keys="[ScooterModel.current_user_id]",
    )
    rentals = relationship("RentalModel", back_populates="user")

    @property
    def max_rentals(self) -> int:
        return 3 if self.user_type == "vip" else 1

    @property
    def rented_scooter_ids(self) -> List[int]:
        if "rented_scooters" in self.__dict__:
            return [sc.id for sc in self.rented_scooters]
        from sqlalchemy.orm import object_session
        s = object_session(self)
        if s is not None and s.is_active:
            try:
                return [sc.id for sc in self.rented_scooters]
            except Exception:
                pass
        try:
            from app.dependencies import get_repository
            fresh = get_repository().find_user_by_id(self.id)
            if fresh and "rented_scooters" in fresh.__dict__:
                return [sc.id for sc in fresh.rented_scooters]
        except Exception:
            pass
        return []

    def can_rent(self) -> bool:
        return len(self.rented_scooter_ids) < self.max_rentals

    def to_dict(self) -> Dict[str, Any]:
        scooters = []
        if "rented_scooters" in self.__dict__ and self.rented_scooters:
            scooters = [
                {
                    "id": s.id,
                    "model": s.model,
                    "charge_level": s.charge_level,
                    "status": s.status,
                }
                for s in self.rented_scooters
            ]
        return {
            "id": self.id,
            "name": self.name,
            "user_type": self.user_type,
            "max_rentals": self.max_rentals,
            "rented_scooter_ids": self.rented_scooter_ids,
            "rented_scooters": scooters,
        }


class RegularUser(metaclass=UserTypeMeta):
    max_rentals = 1

    def __new__(cls, *args, **kwargs):
        kwargs["user_type"] = "regular"
        return UserModel(*args, **kwargs)


class VipUser(metaclass=UserTypeMeta):
    max_rentals = 3

    def __new__(cls, *args, **kwargs):
        kwargs["user_type"] = "vip"
        return UserModel(*args, **kwargs)


def create_user_instance(user_id: Optional[int], name: str, user_type: str) -> UserModel:
    if not isinstance(user_type, str):
        raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")
    clean_type = user_type.strip().lower()
    if clean_type == "regular":
        user = RegularUser(name=name)
    elif clean_type == "vip":
        user = VipUser(name=name)
    else:
        raise ValidationError(
            f"Неизвестный тип пользователя '{user_type}'. Допустимые типы: 'regular', 'vip'."
        )
    if user_id is not None:
        user.id = user_id
    return user


class ScooterModel(Base):
    __tablename__ = "scooters"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    model = Column(String, nullable=False)
    charge_level = Column(Integer, nullable=False, default=100)
    status = Column(String, nullable=False, default="available")
    current_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)

    current_user = relationship(
        "UserModel",
        back_populates="rented_scooters",
        foreign_keys=[current_user_id],
    )
    rentals = relationship("RentalModel", back_populates="scooter")

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "model": self.model,
            "charge_level": self.charge_level,
            "status": self.status,
            "current_user_id": self.current_user_id,
        }
        if "current_user" in self.__dict__ and self.current_user is not None:
            data["current_user"] = {
                "id": self.current_user.id,
                "name": self.current_user.name,
                "user_type": self.current_user.user_type,
            }
        else:
            data["current_user"] = None
        return data


class RentalModel(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    scooter_id = Column(Integer, ForeignKey("scooters.id", ondelete="SET NULL"), nullable=True)
    user_name = Column(String, nullable=True)
    scooter_model = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    battery_used = Column(Integer, nullable=True, default=0)

    user = relationship("UserModel", back_populates="rentals")
    scooter = relationship("ScooterModel", back_populates="rentals")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "scooter_id": self.scooter_id,
            "status": self.status,
            "battery_used": self.battery_used,
            "user_name": self.user.name if self.user else self.user_name,
            "scooter_model": self.scooter.model if self.scooter else self.scooter_model,
        }


User = UserModel
Scooter = ScooterModel
Rental = RentalModel
