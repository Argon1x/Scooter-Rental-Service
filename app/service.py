from typing import Dict, List, Optional
from app.exceptions import DomainRuleError, NotFoundError, ValidationError
from app.models import (
    RegularUser,
    Scooter,
    ScooterStatus,
    User,
    VipUser,
    create_user_instance,
)


class RentalService:
    def __init__(self):
        self._users: Dict[int, User] = {}
        self._scooters: Dict[int, Scooter] = {}
        self._next_user_id: int = 1
        self._next_scooter_id: int = 1

    def create_user(self, name: str, user_type: str = "regular") -> User:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Имя пользователя должно быть непустой строкой.")

        if user_type is None:
            raise ValidationError("Поле 'user_type' не может быть null.")

        if not isinstance(user_type, str):
            raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")

        user_id = self._next_user_id
        self._next_user_id += 1

        user = create_user_instance(user_id=user_id, name=name.strip(), user_type=user_type)
        self._users[user_id] = user
        return user

    def get_user(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(f"Пользователь с ID {user_id} не найден.")
        return user

    def list_users(self, user_type: Optional[str] = None) -> List[User]:
        users = list(self._users.values())
        if user_type:
            clean_type = user_type.strip().lower()
            users = [u for u in users if u.user_type == clean_type]
        return users

    def update_user(
        self,
        user_id: int,
        name: Optional[str] = None,
        user_type: Optional[str] = None,
    ) -> User:
        user = self.get_user(user_id)

        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValidationError("Имя пользователя должно быть непустой строкой.")
            user.name = name.strip()

        if user_type is not None:
            if not isinstance(user_type, str):
                raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")
            clean_type = user_type.strip().lower()
            if clean_type != user.user_type:
                new_user = create_user_instance(user.id, user.name, clean_type)
                if len(user.rented_scooter_ids) > new_user.max_rentals:
                    raise DomainRuleError(
                        f"Нельзя сменить тип на '{clean_type}': у пользователя сейчас "
                        f"{len(user.rented_scooter_ids)} активных аренд, а лимит нового тарифа — {new_user.max_rentals}."
                    )
                new_user.rented_scooter_ids = list(user.rented_scooter_ids)
                self._users[user_id] = new_user
                user = new_user

        return user

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        if user.rented_scooter_ids:
            raise DomainRuleError(
                f"Нельзя удалить пользователя с ID {user_id}, пока за ним числятся "
                f"арендованные самокаты: {user.rented_scooter_ids}."
            )
        del self._users[user_id]

    def create_scooter(self, model: str, charge_level: int = 100) -> Scooter:
        if not isinstance(model, str) or not model.strip():
            raise ValidationError("Модель самоката должна быть непустой строкой.")

        if not isinstance(charge_level, (int, float)) or isinstance(charge_level, bool):
            raise ValidationError("Уровень заряда должен быть числом.")

        charge_int = int(charge_level)
        if charge_int < 0 or charge_int > 100:
            raise ValidationError("Уровень заряда должен быть в диапазоне от 0 до 100.")

        scooter_id = self._next_scooter_id
        self._next_scooter_id += 1

        scooter = Scooter(scooter_id=scooter_id, model=model.strip(), charge_level=charge_int)
        self._scooters[scooter_id] = scooter
        return scooter

    def get_scooter(self, scooter_id: int) -> Scooter:
        scooter = self._scooters.get(scooter_id)
        if not scooter:
            raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")
        return scooter

    def list_scooters(
        self,
        status: Optional[str] = None,
        min_charge: Optional[int] = None,
    ) -> List[Scooter]:
        result = list(self._scooters.values())

        if status:
            clean_status = status.strip().lower()
            result = [s for s in result if s.status.value == clean_status]

        if min_charge is not None:
            result = [s for s in result if s.charge_level >= min_charge]

        return result

    def update_scooter(
        self,
        scooter_id: int,
        model: Optional[str] = None,
        charge_level: Optional[int] = None,
    ) -> Scooter:
        scooter = self.get_scooter(scooter_id)

        if scooter.status == ScooterStatus.RENTED and charge_level is not None:
            raise DomainRuleError(
                f"Нельзя изменять уровень заряда самоката №{scooter_id}, пока он находится в поездке.",
                status_code=409,
            )

        if model is not None:
            if not isinstance(model, str) or not model.strip():
                raise ValidationError("Модель самоката должна быть непустой строкой.")
            scooter.model = model.strip()

        if charge_level is not None:
            if not isinstance(charge_level, (int, float)) or isinstance(charge_level, bool):
                raise ValidationError("Уровень заряда должен быть числом.")
            charge_int = int(charge_level)
            if charge_int < 0 or charge_int > 100:
                raise ValidationError("Уровень заряда должен быть от 0 до 100.")
            scooter.charge_level = charge_int

            if scooter.status != ScooterStatus.RENTED:
                if scooter.charge_level < 20:
                    scooter.status = ScooterStatus.MAINTENANCE
                else:
                    scooter.status = ScooterStatus.AVAILABLE

        return scooter

    def delete_scooter(self, scooter_id: int) -> None:
        scooter = self.get_scooter(scooter_id)
        if scooter.status == ScooterStatus.RENTED:
            raise DomainRuleError(
                f"Нельзя удалить самокат с ID {scooter_id}, так как он сейчас находится в аренде."
            )
        del self._scooters[scooter_id]

    def rent_scooter(self, scooter_id: int, user_id: int) -> Scooter:
        scooter = self.get_scooter(scooter_id)
        user = self.get_user(user_id)

        if scooter.status == ScooterStatus.RENTED:
            raise DomainRuleError(
                f"Самокат №{scooter_id} уже арендован другим пользователем (ID {scooter.current_user_id}).",
                status_code=409,
            )
        if scooter.status == ScooterStatus.MAINTENANCE:
            raise DomainRuleError(
                f"Самокат №{scooter_id} находится на техобслуживании/разряжен и недоступен для поездок.",
                status_code=409,
            )

        if scooter.charge_level < 20:
            raise DomainRuleError(
                f"Заряд самоката №{scooter_id} составляет всего {scooter.charge_level}%. "
                f"Для начала поездки требуется минимум 20%.",
                status_code=422,
            )

        if not user.can_rent():
            raise DomainRuleError(
                f"Пользователь '{user.name}' (тариф '{user.user_type}') уже арендовал "
                f"{len(user.rented_scooter_ids)} самокат(а). Лимит тарифа: {user.max_rentals}.",
                status_code=422,
            )

        scooter.status = ScooterStatus.RENTED
        scooter.current_user_id = user.id
        user.rented_scooter_ids.append(scooter.id)

        return scooter

    def return_scooter(self, scooter_id: int, battery_used: int = 10) -> Scooter:
        scooter = self.get_scooter(scooter_id)

        if scooter.status != ScooterStatus.RENTED:
            raise DomainRuleError(
                f"Самокат №{scooter_id} не находится в аренде (текущий статус: '{scooter.status.value}').",
                status_code=409,
            )

        if not isinstance(battery_used, (int, float)) or isinstance(battery_used, bool) or battery_used < 0:
            raise ValidationError("Расход батареи (battery_used) должен быть неотрицательным числом.")

        scooter.charge_level = max(0, scooter.charge_level - int(battery_used))

        if scooter.current_user_id is not None:
            user = self._users.get(scooter.current_user_id)
            if user and scooter.id in user.rented_scooter_ids:
                user.rented_scooter_ids.remove(scooter.id)
            scooter.current_user_id = None

        if scooter.charge_level < 20:
            scooter.status = ScooterStatus.MAINTENANCE
        else:
            scooter.status = ScooterStatus.AVAILABLE

        return scooter

    def charge_scooter(self, scooter_id: int, amount: int = 50) -> Scooter:
        scooter = self.get_scooter(scooter_id)

        if scooter.status == ScooterStatus.RENTED:
            raise DomainRuleError(
                f"Нельзя заряжать самокат №{scooter_id}, пока он находится в поездке.",
                status_code=409,
            )

        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            raise ValidationError("Значение подзарядки (amount) должно быть положительным числом.")

        scooter.charge_level = min(100, scooter.charge_level + int(amount))

        if scooter.status == ScooterStatus.MAINTENANCE and scooter.charge_level >= 20:
            scooter.status = ScooterStatus.AVAILABLE

        return scooter

    def seed_initial_data(self) -> None:
        self.create_user(name="Иван Иванов", user_type="regular")
        self.create_user(name="Анна Смирнова", user_type="vip")

        self.create_scooter(model="Ninebot KickScooter Max", charge_level=90)
        self.create_scooter(model="Xiaomi Electric Scooter 4 Pro", charge_level=75)
        self.create_scooter(model="Kugoo Kirin M4", charge_level=10)
