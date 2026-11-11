#!/usr/bin/env bash

BASE_URL="http://localhost:8080"

echo "=== 1. Healthcheck GET /ping ==="
curl -i -X GET "${BASE_URL}/ping"
echo ""

echo "=== 2. Healthcheck POST /ping (Method Not Allowed) ==="
curl -i -X POST "${BASE_URL}/ping"
echo ""

echo "=== 3. Root API info GET / ==="
curl -i -X GET "${BASE_URL}/"
echo ""

echo "=== 4. List all users GET /api/users ==="
curl -i -X GET "${BASE_URL}/api/users"
echo ""

echo "=== 5. Filter users GET /api/users?type=vip ==="
curl -i -X GET "${BASE_URL}/api/users?type=vip"
echo ""

echo "=== 6. Create user POST /api/users ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Дмитрий Кузнецов", "user_type": "regular"}'
echo ""

echo "=== 7. Create user error: empty name POST /api/users ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "", "user_type": "regular"}'
echo ""

echo "=== 8. Create user error: unknown type POST /api/users ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "user_type": "super_vip"}'
echo ""

echo "=== 9. Create user error: null user_type POST /api/users ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тест", "user_type": null}'
echo ""

echo "=== 10. Get user by ID GET /api/users/1 ==="
curl -i -X GET "${BASE_URL}/api/users/1"
echo ""

echo "=== 11. Get non-existent user GET /api/users/999 ==="
curl -i -X GET "${BASE_URL}/api/users/999"
echo ""

echo "=== 12. Update user PUT /api/users/1 ==="
curl -i -X PUT "${BASE_URL}/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Иван Петрович Иванов"}'
echo ""

echo "=== 13. List all scooters GET /api/scooters ==="
curl -i -X GET "${BASE_URL}/api/scooters"
echo ""

echo "=== 14. Filter scooters by status GET /api/scooters?status=available ==="
curl -i -X GET "${BASE_URL}/api/scooters?status=available"
echo ""

echo "=== 15. Filter scooters by min_charge GET /api/scooters?min_charge=80 ==="
curl -i -X GET "${BASE_URL}/api/scooters?min_charge=80"
echo ""

echo "=== 16. Create scooter POST /api/scooters ==="
curl -i -X POST "${BASE_URL}/api/scooters" \
  -H "Content-Type: application/json" \
  -d '{"model": "Whoosh S1", "charge_level": 85}'
echo ""

echo "=== 17. Create scooter error: charge > 100 POST /api/scooters ==="
curl -i -X POST "${BASE_URL}/api/scooters" \
  -H "Content-Type: application/json" \
  -d '{"model": "Broken", "charge_level": 150}'
echo ""

echo "=== 18. Get scooter by ID GET /api/scooters/1 ==="
curl -i -X GET "${BASE_URL}/api/scooters/1"
echo ""

echo "=== 19. Domain operation: Rent scooter #1 by user #1 POST /api/scooters/1/rent ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
echo ""

echo "=== 20. Domain rule error: Cannot update charge of rented scooter via PUT /api/scooters/1 ==="
curl -i -X PUT "${BASE_URL}/api/scooters/1" \
  -H "Content-Type: application/json" \
  -d '{"charge_level": 95}'
echo ""

echo "=== 21. Domain rule error: Rent already rented scooter POST /api/scooters/1/rent ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'
echo ""

echo "=== 22. Domain rule error: Regular user exceeded limit (max 1) POST /api/scooters/2/rent ==="
curl -i -X POST "${BASE_URL}/api/scooters/2/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
echo ""

echo "=== 23. Domain rule error: Rent discharged scooter #3 (< 20%) POST /api/scooters/3/rent ==="
curl -i -X POST "${BASE_URL}/api/scooters/3/rent" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'
echo ""

echo "=== 24. Domain rule error: Cannot delete user with active rental DELETE /api/users/1 ==="
curl -i -X DELETE "${BASE_URL}/api/users/1"
echo ""

echo "=== 25. Domain rule error: Cannot delete rented scooter DELETE /api/scooters/1 ==="
curl -i -X DELETE "${BASE_URL}/api/scooters/1"
echo ""

echo "=== 26. Domain operation: Return scooter #1 POST /api/scooters/1/return ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/return" \
  -H "Content-Type: application/json" \
  -d '{"battery_used": 20}'
echo ""

echo "=== 27. Domain rule error: Return unrented scooter POST /api/scooters/1/return ==="
curl -i -X POST "${BASE_URL}/api/scooters/1/return" \
  -H "Content-Type: application/json" \
  -d '{"battery_used": 5}'
echo ""

echo "=== 28. Domain operation: Charge discharged scooter #3 POST /api/scooters/3/charge ==="
curl -i -X POST "${BASE_URL}/api/scooters/3/charge" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}'
echo ""

echo "=== 29. Charge error: invalid amount POST /api/scooters/3/charge ==="
curl -i -X POST "${BASE_URL}/api/scooters/3/charge" \
  -H "Content-Type: application/json" \
  -d '{"amount": -10}'
echo ""

echo "=== 30. Malformed JSON error POST /api/users ==="
curl -i -X POST "${BASE_URL}/api/users" \
  -H "Content-Type: application/json" \
  -d '{invalid_json}'
echo ""

echo "=== 31. Unknown route GET /api/unknown ==="
curl -i -X GET "${BASE_URL}/api/unknown"
echo ""

echo "=== 32. Delete user DELETE /api/users/3 ==="
curl -i -X DELETE "${BASE_URL}/api/users/3"
echo ""

echo "=== 33. Atomic update test: user update with invalid type PUT /api/users/1 ==="
curl -i -X PUT "${BASE_URL}/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Некорректная Попытка", "user_type": "bad_type"}'
echo ""

echo "=== 34. Check user #1 name was NOT changed after failed update GET /api/users/1 ==="
curl -i -X GET "${BASE_URL}/api/users/1"
echo ""
