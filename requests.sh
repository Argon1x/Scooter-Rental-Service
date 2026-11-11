#!/usr/bin/env bash

BASE_URL="http://localhost:8080"

echo "=== 1. Проверка работы сервиса GET /ping ==="
curl -i -X GET "${BASE_URL}/ping"
echo ""

echo "=== 2. Ошибка метода POST /ping ==="
curl -i -X POST "${BASE_URL}/ping"
echo ""

echo "=== 3. Информация о сервисе GET / ==="
curl -i -X GET "${BASE_URL}/"
echo ""

echo "=== 4. Список пользователей GET /api/users ==="
curl -i -X GET "${BASE_URL}/api/users"
echo ""

echo "=== 5. Фильтрация пользователей по VIP GET /api/users?type=vip ==="
curl -i -X GET "${BASE_URL}/api/users?type=vip"
echo ""

echo "=== 6. Создание пользователя POST /api/users ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Дмитрий Кузнецов", "user_type": "regular"}'
echo ""

echo "=== 7. Ошибка: пустое имя пользователя ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "", "user_type": "regular"}'
echo ""

echo "=== 8. Ошибка: неизвестный тариф ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "user_type": "super_vip"}'
echo ""

echo "=== 9. Ошибка: тариф null ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "user_type": null}'
echo ""

echo "=== 10. Получение пользователя по ID ==="
curl -i -X GET "${BASE_URL}/api/users/1"
echo ""

echo "=== 11. Ошибка: несуществующий пользователь ==="
curl -i -X GET "${BASE_URL}/api/users/999"
echo ""

echo "=== 12. Обновление имени пользователя ==="
curl -i -X PUT "${BASE_URL}/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Иван Петрович Иванов"}'
echo ""

echo "=== 13. Список самокатов GET /api/scooters ==="
curl -i -X GET "${BASE_URL}/api/scooters"
echo ""

echo "=== 14. Фильтрация доступных самокатов ==="
curl -i -X GET "${BASE_URL}/api/scooters?status=available"
echo ""

echo "=== 15. Фильтрация по минимальному заряду ==="
curl -i -X GET "${BASE_URL}/api/scooters?min_charge=80"
echo ""

echo "=== 16. Создание нового самоката ==="
curl -i -X POST "${BASE_URL}/api/scooters" \
  -H "Content-Type: application/json" \
  -d '{"model": "Whoosh S1", "charge_level": 85}'
echo ""

echo "=== 17. Ошибка: заряд больше 100 ==="
curl -i -X POST "${BASE_URL}/api/scooters" \
  -H "Content-Type: application/json" \
  -d '{"model": "Broken", "charge_level": 150}'
echo ""

echo "=== 18. Получение самоката по ID ==="
curl -i -X GET "${BASE_URL}/api/scooters/1"
echo ""

echo "=== 19. Аренда самоката 1 пользователем 1 ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
echo ""

echo "=== 20. Ошибка: изменение заряда у самоката в поездке ==="
curl -i -X PUT "${BASE_URL}/api/scooters/1" \
  -H "Content-Type: application/json" \
  -d '{"charge_level": 95}'
echo ""

echo "=== 21. Ошибка: повторная аренда уже занятого самоката ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'
echo ""

echo "=== 22. Ошибка: превышение лимита аренд для regular (максимум 1) ==="
curl -i -X POST "${BASE_URL}/api/scooters/2/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
echo ""

echo "=== 23. Ошибка: аренда разряженного самоката (< 20%) ==="
curl -i -X POST "${BASE_URL}/api/scooters/3/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'
echo ""

echo "=== 24. Ошибка: удаление пользователя с активной арендой ==="
curl -i -X DELETE "${BASE_URL}/api/users/1"
echo ""

echo "=== 25. Ошибка: удаление самоката в аренде ==="
curl -i -X DELETE "${BASE_URL}/api/scooters/1"
echo ""

echo "=== 26. Возврат самоката 1 ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/return" \
  -H "Content-Type: application/json" \
  -d '{"battery_used": 20}'
echo ""

echo "=== 27. Ошибка: возврат неарендованного самоката ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/return" \
  -H "Content-Type: application/json" \
  -d '{"battery_used": 5}'
echo ""

echo "=== 28. Зарядка разряженного самоката ==="
curl -i -X POST "${BASE_URL}/api/scooters/3/charge" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}'
echo ""

echo "=== 29. Ошибка: отрицательное значение зарядки ==="
curl -i -X POST "${BASE_URL}/api/scooters/3/charge" \
  -H "Content-Type: application/json" \
  -d '{"amount": -10}'
echo ""

echo "=== 30. Ошибка: невалидный JSON ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{invalid_json}'
echo ""

echo "=== 31. Несуществующий эндпоинт ==="
curl -i -X GET "${BASE_URL}/api/unknown"
echo ""

echo "=== 32. Удаление пользователя 3 ==="
curl -i -X DELETE "${BASE_URL}/api/users/3"
echo ""

echo "=== 33. Ошибка атомарности: неверный тариф при обновлении ==="
curl -i -X PUT "${BASE_URL}/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Некорректная Попытка", "user_type": "bad_type"}'
echo ""

echo "=== 34. Проверка: имя пользователя не изменилось после ошибки ==="
curl -i -X GET "${BASE_URL}/api/users/1"
echo ""
