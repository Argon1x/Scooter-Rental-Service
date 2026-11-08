import logging
import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
from app.exceptions import AppException
from app.routers.scooters import router as scooters_router
from app.routers.users import router as users_router

logger = logging.getLogger("scooter_app")

app = FastAPI(
    title="Scooter Rental Service",
    description="HTTP-сервис аренды электросамокатов на FastAPI для Задания 2",
    version="2.0.0",
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    msg = first_error.get("msg", "Некорректный формат данных.")
    field = ".".join(str(loc) for loc in first_error.get("loc", []) if loc != "body")
    error_text = f"Ошибка в поле '{field}': {msg}" if field else msg
    return JSONResponse(
        status_code=400,
        content={"error": error_text, "status": 400},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Непредвиденная внутренняя ошибка: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Внутренняя ошибка сервера.", "status": 500},
    )


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/")
def root():
    return {
        "service": "Scooter Rental Service (FastAPI)",
        "version": "2.0.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "endpoints": {
            "healthcheck": "GET /ping",
            "users": "GET, POST /api/users, GET, PUT, DELETE /api/users/{id}",
            "scooters": "GET, POST /api/scooters, GET, PUT, DELETE /api/scooters/{id}",
            "operations": "POST /api/scooters/{id}/rent, POST /api/scooters/{id}/return, POST /api/scooters/{id}/charge",
        },
    }


app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(scooters_router, prefix="/api/scooters", tags=["Scooters"])

if __name__ == "__main__":
    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
