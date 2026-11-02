from http.server import BaseHTTPRequestHandler
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from app.exceptions import AppException, ValidationError
from app.service import RentalService

logger = logging.getLogger("scooter_server")


class ScooterRequestHandler(BaseHTTPRequestHandler):
    service: RentalService = None

    def log_message(self, format_str: str, *args: Any) -> None:
        logger.info("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format_str % args)

    def _send_json(self, status_code: int, data: Any, extra_headers: Optional[Dict[str, str]] = None) -> None:
        try:
            body_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body_bytes)))
            if extra_headers:
                for k, v in extra_headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body_bytes)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_error(self, status_code: int, message: str) -> None:
        self._send_json(status_code, {"error": message, "status": status_code})

    def _read_json_body(self) -> Dict[str, Any]:
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            raise ValidationError("Отсутствует заголовок Content-Length или тело запроса пустое.")

        try:
            content_length = int(content_length_header)
        except ValueError:
            raise ValidationError("Некорректное значение заголовка Content-Length.")

        if content_length <= 0:
            raise ValidationError("Тело запроса пустое.")

        try:
            raw_body = self.rfile.read(content_length).decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("Тело запроса должно быть в кодировке UTF-8.")

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Некорректный синтаксис JSON: {e.msg} (строка {e.lineno}, колонка {e.colno}).")

        if not isinstance(data, dict):
            raise ValidationError("Тело запроса должно быть JSON-объектом (словарём).")

        return data

    def _parse_int_id(self, raw_id: str, entity_name: str = "ID") -> int:
        try:
            val = int(raw_id)
            if val <= 0:
                raise ValueError()
            return val
        except ValueError:
            raise ValidationError(f"{entity_name} должен быть положительным целым числом, получено '{raw_id}'.")

    def do_GET(self) -> None:
        self._handle_request_safe("GET")

    def do_POST(self) -> None:
        self._handle_request_safe("POST")

    def do_PUT(self) -> None:
        self._handle_request_safe("PUT")

    def do_DELETE(self) -> None:
        self._handle_request_safe("DELETE")

    def _handle_request_safe(self, method: str) -> None:
        try:
            self._dispatch_route(method)
        except AppException as e:
            self._send_error(e.status_code, e.message)
        except Exception as e:
            logger.exception("Непредвиденная внутренняя ошибка: %s", e)
            self._send_error(500, f"Внутренняя ошибка сервера: {str(e)}")

    def _dispatch_route(self, method: str) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        segments = [seg for seg in path.split("/") if seg]
        query_params = parse_qs(parsed_url.query)

        if segments == ["ping"]:
            if method != "GET":
                self._send_method_not_allowed("GET")
                return
            self._send_json(200, {"message": "pong"})
            return

        if not segments:
            if method != "GET":
                self._send_method_not_allowed("GET")
                return
            self._send_json(200, {
                "service": "Scooter Rental Service",
                "version": "1.0.0",
                "docs": {
                    "healthcheck": "GET /ping",
                    "users": {
                        "list": "GET /api/users?type=regular|vip",
                        "get": "GET /api/users/{id}",
                        "create": "POST /api/users",
                        "update": "PUT /api/users/{id}",
                        "delete": "DELETE /api/users/{id}",
                    },
                    "scooters": {
                        "list": "GET /api/scooters?status=available|rented|maintenance&min_charge=50",
                        "get": "GET /api/scooters/{id}",
                        "create": "POST /api/scooters",
                        "update": "PUT /api/scooters/{id}",
                        "delete": "DELETE /api/scooters/{id}",
                    },
                    "operations": {
                        "rent": "POST /api/scooters/{id}/rent",
                        "return": "POST /api/scooters/{id}/return",
                        "charge": "POST /api/scooters/{id}/charge",
                    }
                }
            })
            return

        if len(segments) >= 2 and segments[0] == "api" and segments[1] == "users":
            self._route_users(method, segments, query_params)
            return

        if len(segments) >= 2 and segments[0] == "api" and segments[1] == "scooters":
            self._route_scooters(method, segments, query_params)
            return

        self._send_error(404, f"Маршрут '{self.path}' не найден.")

    def _send_method_not_allowed(self, allowed_methods: str) -> None:
        self._send_json(
            405,
            {"error": f"Метод {self.command} не поддерживается для данного URL.", "status": 405},
            extra_headers={"Allow": allowed_methods},
        )

    def _route_users(self, method: str, segments: List[str], query_params: Dict[str, List[str]]) -> None:
        if len(segments) == 2:
            if method == "GET":
                user_type = query_params.get("type", [None])[0]
                users = self.service.list_users(user_type=user_type)
                self._send_json(200, [u.to_dict() for u in users])
            elif method == "POST":
                data = self._read_json_body()
                name = data.get("name")
                user_type = data.get("user_type", "regular")
                if not name:
                    raise ValidationError("Обязательное поле 'name' отсутствует.")
                user = self.service.create_user(name=name, user_type=user_type)
                self._send_json(201, user.to_dict())
            else:
                self._send_method_not_allowed("GET, POST")
            return

        if len(segments) == 3:
            user_id = self._parse_int_id(segments[2], "ID пользователя")
            if method == "GET":
                user = self.service.get_user(user_id)
                self._send_json(200, user.to_dict())
            elif method == "PUT":
                data = self._read_json_body()
                name = data.get("name")
                user_type = data.get("user_type")
                updated_user = self.service.update_user(user_id, name=name, user_type=user_type)
                self._send_json(200, updated_user.to_dict())
            elif method == "DELETE":
                self.service.delete_user(user_id)
                self._send_json(200, {"message": f"Пользователь с ID {user_id} успешно удален."})
            else:
                self._send_method_not_allowed("GET, PUT, DELETE")
            return

        self._send_error(404, f"Маршрут '{self.path}' не найден.")

    def _route_scooters(self, method: str, segments: List[str], query_params: Dict[str, List[str]]) -> None:
        if len(segments) == 2:
            if method == "GET":
                status = query_params.get("status", [None])[0]
                min_charge_raw = query_params.get("min_charge", [None])[0]
                min_charge = None
                if min_charge_raw is not None:
                    try:
                        min_charge = int(min_charge_raw)
                    except ValueError:
                        raise ValidationError("Параметр 'min_charge' должен быть целым числом.")

                scooters = self.service.list_scooters(status=status, min_charge=min_charge)
                self._send_json(200, [s.to_dict() for s in scooters])
            elif method == "POST":
                data = self._read_json_body()
                model = data.get("model")
                charge_level = data.get("charge_level", 100)
                if not model:
                    raise ValidationError("Обязательное поле 'model' отсутствует.")
                scooter = self.service.create_scooter(model=model, charge_level=charge_level)
                self._send_json(201, scooter.to_dict())
            else:
                self._send_method_not_allowed("GET, POST")
            return

        if len(segments) == 3:
            scooter_id = self._parse_int_id(segments[2], "ID самоката")
            if method == "GET":
                scooter = self.service.get_scooter(scooter_id)
                self._send_json(200, scooter.to_dict())
            elif method == "PUT":
                data = self._read_json_body()
                model = data.get("model")
                charge_level = data.get("charge_level")
                updated_scooter = self.service.update_scooter(scooter_id, model=model, charge_level=charge_level)
                self._send_json(200, updated_scooter.to_dict())
            elif method == "DELETE":
                self.service.delete_scooter(scooter_id)
                self._send_json(200, {"message": f"Самокат с ID {scooter_id} успешно удален."})
            else:
                self._send_method_not_allowed("GET, PUT, DELETE")
            return

        if len(segments) == 4:
            scooter_id = self._parse_int_id(segments[2], "ID самоката")
            action = segments[3].lower()

            if action == "rent":
                if method != "POST":
                    self._send_method_not_allowed("POST")
                    return
                data = self._read_json_body()
                user_id_raw = data.get("user_id")
                if user_id_raw is None:
                    raise ValidationError("Для аренды требуется указать 'user_id' в теле запроса.")
                user_id = self._parse_int_id(str(user_id_raw), "user_id")
                scooter = self.service.rent_scooter(scooter_id=scooter_id, user_id=user_id)
                self._send_json(200, {
                    "message": f"Самокат №{scooter_id} успешно выдан пользователю №{user_id}.",
                    "scooter": scooter.to_dict(),
                })
                return

            elif action == "return":
                if method != "POST":
                    self._send_method_not_allowed("POST")
                    return
                data = self._read_json_body()
                battery_used = data.get("battery_used", 10)
                if not isinstance(battery_used, (int, float)):
                    raise ValidationError("Поле 'battery_used' должно быть числом.")
                scooter = self.service.return_scooter(scooter_id=scooter_id, battery_used=int(battery_used))
                self._send_json(200, {
                    "message": f"Поездка на самокате №{scooter_id} успешно завершена.",
                    "scooter": scooter.to_dict(),
                })
                return

            elif action == "charge":
                if method != "POST":
                    self._send_method_not_allowed("POST")
                    return
                data = self._read_json_body()
                amount = data.get("amount", 50)
                if not isinstance(amount, (int, float)):
                    raise ValidationError("Поле 'amount' должно быть числом.")
                scooter = self.service.charge_scooter(scooter_id=scooter_id, amount=int(amount))
                self._send_json(200, {
                    "message": f"Самокат №{scooter_id} успешно заряжен.",
                    "scooter": scooter.to_dict(),
                })
                return

        self._send_error(404, f"Маршрут '{self.path}' не найден.")
