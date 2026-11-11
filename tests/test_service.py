import unittest
from app.exceptions import DomainRuleError, NotFoundError, ValidationError
from app.models import RegularUser, ScooterStatus, VipUser
from app.repository import InMemoryRepository
from app.service import RentalService


class TestRentalService(unittest.TestCase):

    def setUp(self):
        self.repository = InMemoryRepository()
        self.service = RentalService(repository=self.repository)

    def test_create_and_get_user(self):
        user = self.service.create_user("Алексей", "regular")
        self.assertIsInstance(user, RegularUser)
        self.assertEqual(user.name, "Алексей")
        self.assertEqual(user.max_rentals, 1)

        fetched = self.service.get_user(user.id)
        self.assertEqual(fetched.id, user.id)

    def test_create_vip_user(self):
        user = self.service.create_user("Елена", "vip")
        self.assertIsInstance(user, VipUser)
        self.assertEqual(user.max_rentals, 3)

    def test_create_user_empty_name_fails(self):
        with self.assertRaises(ValidationError):
            self.service.create_user("")

    def test_create_user_null_type_fails(self):
        with self.assertRaises(ValidationError):
            self.service.create_user("Тест", None)

    def test_get_nonexistent_user_fails(self):
        with self.assertRaises(NotFoundError):
            self.service.get_user(999)

    def test_list_users_filter_by_type(self):
        self.service.create_user("Пользователь 1", "regular")
        self.service.create_user("Пользователь 2", "vip")
        self.service.create_user("Пользователь 3", "regular")

        regulars = self.service.list_users(user_type="regular")
        vips = self.service.list_users(user_type="vip")

        self.assertEqual(len(regulars), 2)
        self.assertEqual(len(vips), 1)

    def test_create_and_get_scooter(self):
        scooter = self.service.create_scooter("Ninebot Max", 85)
        self.assertEqual(scooter.model, "Ninebot Max")
        self.assertEqual(scooter.charge_level, 85)
        self.assertEqual(scooter.status, ScooterStatus.AVAILABLE)

        fetched = self.service.get_scooter(scooter.id)
        self.assertEqual(fetched.id, scooter.id)

    def test_create_scooter_low_charge_sets_maintenance(self):
        scooter = self.service.create_scooter("Ninebot Discharged", 10)
        self.assertEqual(scooter.status, ScooterStatus.MAINTENANCE)

    def test_list_scooters_filtering(self):
        self.service.create_scooter("Самокат A", 100)
        self.service.create_scooter("Самокат B", 50)
        self.service.create_scooter("Самокат C", 10)

        available = self.service.list_scooters(status="available")
        self.assertEqual(len(available), 2)

        high_charge = self.service.list_scooters(min_charge=80)
        self.assertEqual(len(high_charge), 1)
        self.assertEqual(high_charge[0].model, "Самокат A")

    def test_successful_rental(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 90)

        rented = self.service.rent_scooter(scooter.id, user.id)
        self.assertEqual(rented.status, ScooterStatus.RENTED)
        self.assertEqual(rented.current_user_id, user.id)
        self.assertIn(scooter.id, user.rented_scooter_ids)

    def test_regular_user_cannot_rent_more_than_one_scooter(self):
        user = self.service.create_user("Иван", "regular")
        scooter1 = self.service.create_scooter("Ninebot 1", 90)
        scooter2 = self.service.create_scooter("Ninebot 2", 90)

        self.service.rent_scooter(scooter1.id, user.id)

        with self.assertRaises(DomainRuleError):
            self.service.rent_scooter(scooter2.id, user.id)

    def test_vip_user_can_rent_up_to_three_scooters(self):
        vip = self.service.create_user("Анна VIP", "vip")
        s1 = self.service.create_scooter("Ninebot 1", 90)
        s2 = self.service.create_scooter("Ninebot 2", 90)
        s3 = self.service.create_scooter("Ninebot 3", 90)
        s4 = self.service.create_scooter("Ninebot 4", 90)

        self.service.rent_scooter(s1.id, vip.id)
        self.service.rent_scooter(s2.id, vip.id)
        self.service.rent_scooter(s3.id, vip.id)
        self.assertEqual(len(vip.rented_scooter_ids), 3)

        with self.assertRaises(DomainRuleError):
            self.service.rent_scooter(s4.id, vip.id)

    def test_cannot_rent_already_rented_scooter(self):
        u1 = self.service.create_user("Иван", "regular")
        u2 = self.service.create_user("Петр", "regular")
        scooter = self.service.create_scooter("Ninebot", 90)

        self.service.rent_scooter(scooter.id, u1.id)

        with self.assertRaises(DomainRuleError):
            self.service.rent_scooter(scooter.id, u2.id)

    def test_cannot_rent_low_charge_scooter(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 18)

        with self.assertRaises(DomainRuleError):
            self.service.rent_scooter(scooter.id, user.id)

    def test_successful_return_normal_battery(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 90)
        self.service.rent_scooter(scooter.id, user.id)

        returned = self.service.return_scooter(scooter.id, battery_used=30)
        self.assertEqual(returned.status, ScooterStatus.AVAILABLE)
        self.assertEqual(returned.charge_level, 60)
        self.assertIsNone(returned.current_user_id)
        self.assertEqual(len(user.rented_scooter_ids), 0)

    def test_return_discharges_to_maintenance(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 30)
        self.service.rent_scooter(scooter.id, user.id)

        returned = self.service.return_scooter(scooter.id, battery_used=15)
        self.assertEqual(returned.status, ScooterStatus.MAINTENANCE)
        self.assertEqual(returned.charge_level, 15)

    def test_return_unrented_scooter_fails(self):
        scooter = self.service.create_scooter("Ninebot", 90)
        with self.assertRaises(DomainRuleError):
            self.service.return_scooter(scooter.id, battery_used=10)

    def test_charge_scooter(self):
        scooter = self.service.create_scooter("Ninebot", 10)
        self.assertEqual(scooter.status, ScooterStatus.MAINTENANCE)

        charged = self.service.charge_scooter(scooter.id, amount=50)
        self.assertEqual(charged.charge_level, 60)
        self.assertEqual(charged.status, ScooterStatus.AVAILABLE)

    def test_cannot_charge_rented_scooter(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 80)
        self.service.rent_scooter(scooter.id, user.id)

        with self.assertRaises(DomainRuleError):
            self.service.charge_scooter(scooter.id, amount=10)

    def test_cannot_update_charge_when_rented(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 80)
        self.service.rent_scooter(scooter.id, user.id)

        with self.assertRaises(DomainRuleError):
            self.service.update_scooter(scooter.id, charge_level=95)

    def test_cannot_delete_user_with_active_rental(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 90)
        self.service.rent_scooter(scooter.id, user.id)

        with self.assertRaises(DomainRuleError):
            self.service.delete_user(user.id)

    def test_cannot_delete_rented_scooter(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 90)
        self.service.rent_scooter(scooter.id, user.id)

        with self.assertRaises(DomainRuleError):
            self.service.delete_scooter(scooter.id)

    def test_update_user_atomic_on_invalid_type(self):
        user = self.service.create_user("Иван", "regular")
        with self.assertRaises(ValidationError):
            self.service.update_user(user.id, name="Новый Иван", user_type="invalid_type")
        fetched = self.service.get_user(user.id)
        self.assertEqual(fetched.name, "Иван")

    def test_update_user_atomic_on_rental_limit_exceeded(self):
        vip = self.service.create_user("Анна", "vip")
        s1 = self.service.create_scooter("Ninebot 1", 90)
        s2 = self.service.create_scooter("Ninebot 2", 90)
        self.service.rent_scooter(s1.id, vip.id)
        self.service.rent_scooter(s2.id, vip.id)
        with self.assertRaises(DomainRuleError):
            self.service.update_user(vip.id, name="Новая Анна", user_type="regular")
        fetched = self.service.get_user(vip.id)
        self.assertEqual(fetched.name, "Анна")
        self.assertEqual(fetched.user_type, "vip")

    def test_update_scooter_atomic_on_invalid_charge(self):
        scooter = self.service.create_scooter("Ninebot", 80)
        with self.assertRaises(ValidationError):
            self.service.update_scooter(scooter.id, model="Новая модель", charge_level=200)
        fetched = self.service.get_scooter(scooter.id)
        self.assertEqual(fetched.model, "Ninebot")

    def test_update_scooter_atomic_on_rented_charge_update(self):
        user = self.service.create_user("Иван", "regular")
        scooter = self.service.create_scooter("Ninebot", 80)
        self.service.rent_scooter(scooter.id, user.id)
        with self.assertRaises(DomainRuleError):
            self.service.update_scooter(scooter.id, model="Новая модель", charge_level=95)
        fetched = self.service.get_scooter(scooter.id)
        self.assertEqual(fetched.model, "Ninebot")

    def test_concurrent_rent_scooter_thread_safety(self):
        import concurrent.futures
        u1 = self.service.create_user("Пользователь 1", "regular")
        u2 = self.service.create_user("Пользователь 2", "regular")
        scooter = self.service.create_scooter("Ninebot", 90)

        results = []
        errors = []

        def try_rent(u_id):
            try:
                res = self.service.rent_scooter(scooter.id, u_id)
                results.append(res)
            except Exception as e:
                errors.append(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(try_rent, u1.id)
            f2 = executor.submit(try_rent, u2.id)
            f1.result()
            f2.result()

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], DomainRuleError)
        fetched = self.service.get_scooter(scooter.id)
        self.assertEqual(fetched.status, ScooterStatus.RENTED)


if __name__ == "__main__":
    unittest.main()
