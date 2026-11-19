import unittest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import app.dependencies as deps
from app.database import Base
from app.exceptions import DomainRuleError, NotFoundError
from app.models import RentalModel, ScooterModel, ScooterStatus, UserModel
from app.repository import SqlAlchemyRepository
from app.service import RentalService


class TestDatabaseRequirements(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine,
        )
        self.repository = SqlAlchemyRepository(session_factory=self.session_factory)
        self.service = RentalService(repository=self.repository)
        deps._repository = self.repository
        deps._service = self.service

    def tearDown(self):
        Base.metadata.drop_all(self.engine)

    def test_related_objects_lifecycle_and_history(self):
        user = self.service.create_user("Дмитрий", "regular")
        scooter = self.service.create_scooter("Ninebot Max", 90)

        rented = self.service.rent_scooter(scooter.id, user.id)
        self.assertEqual(rented.status, ScooterStatus.RENTED.value)
        self.assertEqual(rented.current_user_id, user.id)

        rentals = self.service.list_rentals()
        self.assertEqual(len(rentals), 1)
        self.assertEqual(rentals[0].user_id, user.id)
        self.assertEqual(rentals[0].scooter_id, scooter.id)
        self.assertEqual(rentals[0].user_name, "Дмитрий")
        self.assertEqual(rentals[0].scooter_model, "Ninebot Max")
        self.assertEqual(rentals[0].status, "active")

        returned = self.service.return_scooter(scooter.id, battery_used=25)
        self.assertEqual(returned.status, ScooterStatus.AVAILABLE.value)
        self.assertEqual(returned.charge_level, 65)
        self.assertIsNone(returned.current_user_id)

        rentals_after = self.service.list_rentals()
        self.assertEqual(len(rentals_after), 1)
        self.assertEqual(rentals_after[0].status, "completed")
        self.assertEqual(rentals_after[0].battery_used, 25)

    def test_rental_history_preserved_after_user_and_scooter_deleted(self):
        user = self.service.create_user("Дмитрий", "regular")
        scooter = self.service.create_scooter("Ninebot Max", 90)

        self.service.rent_scooter(scooter.id, user.id)
        self.service.return_scooter(scooter.id, battery_used=20)

        self.service.delete_user(user.id)
        self.service.delete_scooter(scooter.id)

        rentals = self.service.list_rentals()
        self.assertEqual(len(rentals), 1)
        r = rentals[0]
        self.assertEqual(r.status, "completed")
        self.assertIsNone(r.user_id)
        self.assertIsNone(r.scooter_id)
        self.assertEqual(r.user_name, "Дмитрий")
        self.assertEqual(r.scooter_model, "Ninebot Max")
        self.assertEqual(r.battery_used, 20)
        self.assertEqual(r.to_dict()["user_name"], "Дмитрий")
        self.assertEqual(r.to_dict()["scooter_model"], "Ninebot Max")

    def test_transaction_rollback_prevents_partial_changes(self):
        user = self.service.create_user("Сергей", "regular")
        scooter = self.service.create_scooter("Xiaomi", 80)

        def failing_operation():
            with self.repository.session_factory() as session:
                with session.begin():
                    s = session.query(ScooterModel).filter(ScooterModel.id == scooter.id).first()
                    s.status = ScooterStatus.RENTED.value
                    s.current_user_id = user.id
                    rental = RentalModel(
                        user_id=user.id,
                        scooter_id=scooter.id,
                        user_name=user.name,
                        scooter_model=scooter.model,
                        status="active",
                    )
                    session.add(rental)
                    raise RuntimeError("Имитация сбоя в середине транзакции")

        with self.assertRaises(RuntimeError):
            failing_operation()

        fresh_scooter = self.service.get_scooter(scooter.id)
        self.assertEqual(fresh_scooter.status, ScooterStatus.AVAILABLE.value)
        self.assertIsNone(fresh_scooter.current_user_id)

        rentals = self.service.list_rentals()
        self.assertEqual(len(rentals), 0)

        fresh_user = self.service.get_user(user.id)
        self.assertEqual(len(fresh_user.rented_scooter_ids), 0)

    def test_data_integrity_delete_restriction(self):
        user = self.service.create_user("Ольга", "regular")
        scooter = self.service.create_scooter("Whoosh", 90)
        self.service.rent_scooter(scooter.id, user.id)

        with self.assertRaises(DomainRuleError):
            self.service.delete_user(user.id)

        with self.assertRaises(DomainRuleError):
            self.service.delete_scooter(scooter.id)

        self.service.return_scooter(scooter.id, battery_used=10)
        self.service.delete_scooter(scooter.id)
        with self.assertRaises(NotFoundError):
            self.service.get_scooter(scooter.id)

        self.service.delete_user(user.id)
        with self.assertRaises(NotFoundError):
            self.service.get_user(user.id)

        rentals = self.service.list_rentals()
        self.assertEqual(len(rentals), 1)
        self.assertEqual(rentals[0].status, "completed")

    def test_n_plus_one_avoidance_on_large_dataset(self):
        for i in range(1, 35):
            u = self.service.create_user(f"Пользователь {i}", "regular")
            s = self.service.create_scooter(f"Самокат {i}", 85)
            if i <= 15:
                self.service.rent_scooter(s.id, u.id)

        query_count = 0

        def count_query(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        event.listen(self.engine, "before_cursor_execute", count_query)
        try:
            users = self.repository.find_all_users()
            self.assertEqual(len(users), 34)
            for u in users:
                _ = len(u.rented_scooter_ids)
            self.assertEqual(query_count, 1)

            query_count = 0
            scooters = self.repository.find_all_scooters()
            self.assertEqual(len(scooters), 34)
            for s in scooters:
                _ = s.current_user
            self.assertEqual(query_count, 1)
        finally:
            event.remove(self.engine, "before_cursor_execute", count_query)


if __name__ == "__main__":
    unittest.main()
