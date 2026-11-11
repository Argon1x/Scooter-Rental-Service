import threading
from typing import List, Optional
from app.exceptions import DomainRuleError, NotFoundError, ValidationError
from app.models import (
    RegularUser,
    Scooter,
    ScooterStatus,
    User,
    VipUser,
    create_user_instance,
)
from app.repository import InMemoryRepository


class RentalService:
    def __init__(self, repository: InMemoryRepository):
        self._repo = repository
        self._lock = threading.RLock()

    def create_user(self, name: str, user_type: str = "regular") -> User:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Имя пользователя должно быть непустой строкой.")

        if user_type is None:
            raise ValidationError("Поле 'user_type' не может быть null.")

        if not isinstance(user_type, str):
            raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")

        clean_type = user_type.strip().lower()
        if clean_type not in ("regular", "vip"):
            raise ValidationError(
                f"Неизвестный тип пользователя '{user_type}'. Допустимые типы: 'regular', 'vip'."
            )

        with self._lock:
            user_id = self._repo.get_next_user_id()
            user = create_user_instance(user_id=user_id, name=name.strip(), user_type=clean_type)
            return self._repo.save_user(user)

    def get_user(self, user_id: int) -> User:
        with self._lock:
            user = self._repo.find_user_by_id(user_id)
            if not user:
                raise NotFoundError(f"Пользователь с ID {user_id} не найден.")
            return user

    def list_users(self, user_type: Optional[str] = None) -> List[User]:
        with self._lock:
            users = self._repo.find_all_users()
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
        with self._lock:
            user = self.get_user(user_id)

            clean_name = None
            if name is not None:
                if not isinstance(name, str) or not name.strip():
                    raise ValidationError("Имя пользователя должно быть непустой строкой.")
                clean_name = name.strip()

            new_user_type = None
            if user_type is not None:
                if not isinstance(user_type, str):
                    raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")
                clean_type = user_type.strip().lower()
                if clean_type not in ("regular", "vip"):
                    raise ValidationError(
                        f"Неизвестный тип пользователя '{user_type}'. Допустимые типы: 'regular', 'vip'."
                    )
                if clean_type != user.user_type:
                    target_name = clean_name if clean_name is not None else user.name
                    target_user = create_user_instance(user.id, target_name, clean_type)
                    if len(user.rented_scooter_ids) > target_user.max_rentals:
                        raise DomainRuleError(
                            f"Нельзя сменить тип на '{clean_type}': у пользователя сейчас "
                            f"{len(user.rented_scooter_ids)} активных аренд, а лимит нового тарифа — {target_user.max_rentals}."
                        )
                    new_user_type = clean_type

            if new_user_type is not None:
                final_name = clean_name if clean_name is not None else user.name
                new_user = create_user_instance(user.id, final_name, new_user_type)
                new_user.rented_scooter_ids = list(user.rented_scooter_ids)
                self._repo.save_user(new_user)
                return new_user
            else:
                if clean_name is not None:
                    user.name = clean_name
                self._repo.save_user(user)
                return user

    def delete_user(self, user_id: int) -> None:
        with self._lock:
            user = self.get_user(user_id)
            if user.rented_scooter_ids:
                raise DomainRuleError(
                    f"Нельзя удалить пользователя с ID {user_id}, пока за ним числятся "
                    f"арендованные самокаты: {user.rented_scooter_ids}."
                )
            self._repo.delete_user_by_id(user_id)

    def create_scooter(self, model: str, charge_level: int = 100) -> Scooter:
        if not isinstance(model, str) or not model.strip():
            raise ValidationError("Модель самоката должна быть непустой строкой.")

        if not isinstance(charge_level, (int, float)) or isinstance(charge_level, bool):
            raise ValidationError("Уровень заряда должен быть числом.")

        charge_int = int(charge_level)
        if charge_int < 0 or charge_int > 100:
            raise ValidationError("Уровень заряда должен быть в диапазоне от 0 до 100.")

        with self._lock:
            scooter_id = self._repo.get_next_scooter_id()
            scooter = Scooter(scooter_id=scooter_id, model=model.strip(), charge_level=charge_int)
            return self._repo.save_scooter(scooter)

    def get_scooter(self, scooter_id: int) -> Scooter:
        with self._lock:
            scooter = self._repo.find_scooter_by_id(scooter_id)
            if not scooter:
                raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")
            return scooter

    def list_scooters(
        self,
        status: Optional[str] = None,
        min_charge: Optional[int] = None,
    ) -> List[Scooter]:
        with self._lock:
            result = self._repo.find_all_scooters()

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
        with self._lock:
            scooter = self.get_scooter(scooter_id)

            clean_model = None
            if model is not None:
                if not isinstance(model, str) or not model.strip():
                    raise ValidationError("Модель самоката должна быть непустой строкой.")
                clean_model = model.strip()

            clean_charge = None
            if charge_level is not None:
                if not isinstance(charge_level, (int, float)) or isinstance(charge_level, bool):
                    raise ValidationError("Уровень заряда должен быть числом.")
                charge_int = int(charge_level)
                if charge_int < 0 or charge_int > 100:
                    raise ValidationError("Уровень заряда должен быть от 0 до 100.")
                if scooter.status == ScooterStatus.RENTED:
                    raise DomainRuleError(
                        f"Нельзя изменять уровень заряда самоката №{scooter_id}, пока он находится в поездке.",
                        status_code=409,
                    )
                clean_charge = charge_int

            if clean_model is not None:
                scooter.model = clean_model

            if clean_charge is not None:
                scooter.charge_level = clean_charge
                if scooter.status != ScooterStatus.RENTED:
                    if scooter.charge_level < 20:
                        scooter.status = ScooterStatus.MAINTENANCE
                    else:
                        scooter.status = ScooterStatus.AVAILABLE

            self._repo.save_scooter(scooter)
            return scooter

    def delete_scooter(self, scooter_id: int) -> None:
        with self._lock:
            scooter = self.get_scooter(scooter_id)
            if scooter.status == ScooterStatus.RENTED:
                raise DomainRuleError(
                    f"Нельзя удалить самокат с ID {scooter_id}, так как он сейчас находится в аренде."
                )
            self._repo.delete_scooter_by_id(scooter_id)

    def rent_scooter(self, scooter_id: int, user_id: int) -> Scooter:
        with self._lock:
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
            self._repo.save_scooter(scooter)
            self._repo.save_user(user)

            return scooter

    def return_scooter(self, scooter_id: int, battery_used: int = 10) -> Scooter:
        with self._lock:
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
                user = self._repo.find_user_by_id(scooter.current_user_id)
                if user and scooter.id in user.rented_scooter_ids:
                    user.rented_scooter_ids.remove(scooter.id)
                    self._repo.save_user(user)
                scooter.current_user_id = None

            if scooter.charge_level < 20:
                scooter.status = ScooterStatus.MAINTENANCE
            else:
                scooter.status = ScooterStatus.AVAILABLE

            self._repo.save_scooter(scooter)
            return scooter

    def charge_scooter(self, scooter_id: int, amount: int = 50) -> Scooter:
        with self._lock:
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

            self._repo.save_scooter(scooter)
            return scooter

    def seed_initial_data(self) -> None:
        self.create_user(name="Иван Иванов", user_type="regular")
        self.create_user(name="Анна Смирнова", user_type="vip")

        self.create_scooter(model="Ninebot KickScooter Max", charge_level=90)
        self.create_scooter(model="Xiaomi Electric Scooter 4 Pro", charge_level=75)
        self.create_scooter(model="Kugoo Kirin M4", charge_level=10)
