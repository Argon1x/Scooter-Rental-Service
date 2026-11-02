from http.server import HTTPServer
import os

from app.server import ScooterRequestHandler
from app.service import RentalService


def run_server(port: int = 8080) -> None:
    service = RentalService()
    service.seed_initial_data()

    ScooterRequestHandler.service = service

    server_address = ("", port)
    httpd = HTTPServer(server_address, ScooterRequestHandler)

    print(f"Server started on http://localhost:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080
    run_server(port)
