import threading
from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.exceptions import DomainRuleError, NotFoundError, ValidationError
from app.models import (
    RentalModel,
    ScooterModel,
    ScooterStatus,
    UserModel,
    create_user_instance,
)
from app.repository import SqlAlchemyRepository


class RentalService:
    _lock = threading.RLock()

    def __init__(self, repository: SqlAlchemyRepository):
        self._repo = repository

    def create_user(self, name: str, user_type: str = "regular") -> UserModel:
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

        user = create_user_instance(user_id=None, name=name.strip(), user_type=clean_type)
        return self._repo.save_user(user)

    def get_user(self, user_id: int) -> UserModel:
        user = self._repo.find_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"Пользователь с ID {user_id} не найден.")
        return user

    def list_users(self, user_type: Optional[str] = None) -> List[UserModel]:
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
    ) -> UserModel:
        clean_name = None
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValidationError("Имя пользователя должно быть непустой строкой.")
            clean_name = name.strip()

        clean_type = None
        if user_type is not None:
            if not isinstance(user_type, str):
                raise ValidationError("Поле 'user_type' должно быть строкой ('regular' или 'vip').")
            clean_type = user_type.strip().lower()
            if clean_type not in ("regular", "vip"):
                raise ValidationError(
                    f"Неизвестный тип пользователя '{user_type}'. Допустимые типы: 'regular', 'vip'."
                )

        with self._lock:
            with self._repo.session_factory() as session:
                with session.begin():
                    user = (
                        session.query(UserModel)
                        .with_for_update()
                        .options(joinedload(UserModel.rented_scooters))
                        .filter(UserModel.id == user_id)
                        .first()
                    )
                    if not user:
                        raise NotFoundError(f"Пользователь с ID {user_id} не найден.")

                    if clean_type is not None and clean_type != user.user_type:
                        max_allowed = 3 if clean_type == "vip" else 1
                        if len(user.rented_scooter_ids) > max_allowed:
                            raise DomainRuleError(
                                f"Нельзя сменить тип на '{clean_type}': у пользователя сейчас "
                                f"{len(user.rented_scooter_ids)} активных аренд, а лимит нового тарифа — {max_allowed}."
                            )
                        user.user_type = clean_type

                    if clean_name is not None:
                        user.name = clean_name

                session.refresh(user)
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

    def create_scooter(self, model: str, charge_level: int = 100) -> ScooterModel:
        if not isinstance(model, str) or not model.strip():
            raise ValidationError("Модель самоката должна быть непустой строкой.")

        if not isinstance(charge_level, (int, float)) or isinstance(charge_level, bool):
            raise ValidationError("Уровень заряда должен быть числом.")

        charge_int = int(charge_level)
        if charge_int < 0 or charge_int > 100:
            raise ValidationError("Уровень заряда должен быть в диапазоне от 0 до 100.")

        status = ScooterStatus.AVAILABLE.value if charge_int >= 20 else ScooterStatus.MAINTENANCE.value
        scooter = ScooterModel(model=model.strip(), charge_level=charge_int, status=status)
        return self._repo.save_scooter(scooter)

    def get_scooter(self, scooter_id: int) -> ScooterModel:
        scooter = self._repo.find_scooter_by_id(scooter_id)
        if not scooter:
            raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")
        return scooter

    def list_scooters(
        self,
        status: Optional[str] = None,
        min_charge: Optional[int] = None,
    ) -> List[ScooterModel]:
        scooters = self._repo.find_all_scooters()
        if status:
            clean_status = status.strip().lower()
            scooters = [s for s in scooters if s.status.lower() == clean_status]
        if min_charge is not None:
            scooters = [s for s in scooters if s.charge_level >= min_charge]
        return scooters

    def update_scooter(
        self,
        scooter_id: int,
        model: Optional[str] = None,
        charge_level: Optional[int] = None,
    ) -> ScooterModel:
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
            clean_charge = charge_int

        with self._lock:
            with self._repo.session_factory() as session:
                with session.begin():
                    scooter = (
                        session.query(ScooterModel)
                        .with_for_update()
                        .options(joinedload(ScooterModel.current_user))
                        .filter(ScooterModel.id == scooter_id)
                        .first()
                    )
                    if not scooter:
                        raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")

                    if scooter.status == ScooterStatus.RENTED.value and clean_charge is not None:
                        raise DomainRuleError(
                            f"Нельзя изменять уровень заряда самоката №{scooter_id}, пока он находится в поездке.",
                            status_code=409,
                        )

                    if clean_model is not None:
                        scooter.model = clean_model

                    if clean_charge is not None:
                        scooter.charge_level = clean_charge
                        if scooter.status != ScooterStatus.RENTED.value:
                            if scooter.charge_level < 20:
                                scooter.status = ScooterStatus.MAINTENANCE.value
                            else:
                                scooter.status = ScooterStatus.AVAILABLE.value

                session.refresh(scooter)
                return scooter

    def delete_scooter(self, scooter_id: int) -> None:
        with self._lock:
            scooter = self.get_scooter(scooter_id)
            if scooter.status == ScooterStatus.RENTED.value:
                raise DomainRuleError(
                    f"Нельзя удалить самокат с ID {scooter_id}, так как он сейчас находится в аренде."
                )
            self._repo.delete_scooter_by_id(scooter_id)

    def rent_scooter(self, scooter_id: int, user_id: int) -> ScooterModel:
        with self._lock:
            with self._repo.session_factory() as session:
                with session.begin():
                    scooter = (
                        session.query(ScooterModel)
                        .with_for_update()
                        .options(joinedload(ScooterModel.current_user))
                        .filter(ScooterModel.id == scooter_id)
                        .first()
                    )
                    if not scooter:
                        raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")

                    user = (
                        session.query(UserModel)
                        .with_for_update()
                        .options(joinedload(UserModel.rented_scooters))
                        .filter(UserModel.id == user_id)
                        .first()
                    )
                    if not user:
                        raise NotFoundError(f"Пользователь с ID {user_id} не найден.")

                    if scooter.status == ScooterStatus.RENTED.value:
                        raise DomainRuleError(
                            f"Самокат №{scooter_id} уже арендован другим пользователем (ID {scooter.current_user_id}).",
                            status_code=409,
                        )
                    if scooter.status == ScooterStatus.MAINTENANCE.value:
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

                    scooter.status = ScooterStatus.RENTED.value
                    scooter.current_user_id = user.id

                    rental = RentalModel(
                        user_id=user.id,
                        scooter_id=scooter.id,
                        user_name=user.name,
                        scooter_model=scooter.model,
                        status="active",
                        battery_used=0,
                    )
                    session.add(rental)

                session.refresh(scooter)
                return scooter

    def return_scooter(self, scooter_id: int, battery_used: int = 10) -> ScooterModel:
        if not isinstance(battery_used, (int, float)) or isinstance(battery_used, bool) or battery_used < 0:
            raise ValidationError("Расход батареи (battery_used) должен быть неотрицательным числом.")

        with self._lock:
            with self._repo.session_factory() as session:
                with session.begin():
                    scooter = (
                        session.query(ScooterModel)
                        .with_for_update()
                        .options(joinedload(ScooterModel.current_user))
                        .filter(ScooterModel.id == scooter_id)
                        .first()
                    )
                    if not scooter:
                        raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")

                    if scooter.status != ScooterStatus.RENTED.value:
                        raise DomainRuleError(
                            f"Самокат №{scooter_id} не находится в аренде (текущий статус: '{scooter.status}').",
                            status_code=409,
                        )

                    rental = (
                        session.query(RentalModel)
                        .with_for_update()
                        .filter(RentalModel.scooter_id == scooter_id, RentalModel.status == "active")
                        .first()
                    )
                    if rental:
                        rental.status = "completed"
                        rental.battery_used = int(battery_used)

                    scooter.charge_level = max(0, scooter.charge_level - int(battery_used))
                    scooter.current_user_id = None
                    if scooter.charge_level < 20:
                        scooter.status = ScooterStatus.MAINTENANCE.value
                    else:
                        scooter.status = ScooterStatus.AVAILABLE.value

                session.refresh(scooter)
                return scooter

    def charge_scooter(self, scooter_id: int, amount: int = 50) -> ScooterModel:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
            raise ValidationError("Значение подзарядки (amount) должно быть положительным числом.")

        with self._lock:
            with self._repo.session_factory() as session:
                with session.begin():
                    scooter = (
                        session.query(ScooterModel)
                        .with_for_update()
                        .options(joinedload(ScooterModel.current_user))
                        .filter(ScooterModel.id == scooter_id)
                        .first()
                    )
                    if not scooter:
                        raise NotFoundError(f"Самокат с ID {scooter_id} не найден.")

                    if scooter.status == ScooterStatus.RENTED.value:
                        raise DomainRuleError(
                            f"Нельзя заряжать самокат №{scooter_id}, пока он находится в поездке.",
                            status_code=409,
                        )

                    scooter.charge_level = min(100, scooter.charge_level + int(amount))
                    if scooter.status == ScooterStatus.MAINTENANCE.value and scooter.charge_level >= 20:
                        scooter.status = ScooterStatus.AVAILABLE.value

                session.refresh(scooter)
                return scooter

    def list_rentals(self) -> List[RentalModel]:
        return self._repo.find_all_rentals()

    def seed_initial_data_if_empty(self) -> None:
        with self._repo.session_factory() as session:
            has_users = session.query(UserModel).first() is not None
            has_scooters = session.query(ScooterModel).first() is not None
            if not has_users and not has_scooters:
                self.create_user(name="Иван Иванов", user_type="regular")
                self.create_user(name="Анна Смирнова", user_type="vip")
                self.create_scooter(model="Ninebot KickScooter Max", charge_level=90)
                self.create_scooter(model="Xiaomi Electric Scooter 4 Pro", charge_level=75)
                self.create_scooter(model="Kugoo Kirin M4", charge_level=10)
