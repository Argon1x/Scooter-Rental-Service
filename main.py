from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
from app.database import run_migrations
from app.dependencies import get_service
from app.exceptions import AppException
from app.routers.rentals import router as rentals_router
from app.routers.scooters import router as scooters_router
from app.routers.users import router as users_router

logger = logging.getLogger("scooter_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    service = get_service()
    service.seed_initial_data_if_empty()
    yield


app = FastAPI(
    title="Scooter Rental Service",
    description="HTTP-сервис аренды электросамокатов для Задания 3",
    version="3.0.0",
    lifespan=lifespan,
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
    if errors:
        err = errors[0]
        msg = err.get("msg", "Некорректный формат данных.")
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        field = ".".join(loc)
        if "JSON decode error" in msg:
            error_text = "Некорректный синтаксис JSON."
        elif field:
            error_text = f"Некорректное значение в поле '{field}': {msg}."
        else:
            error_text = msg
    else:
        error_text = "Некорректные данные запроса."

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
        "service": "Scooter Rental Service",
        "version": "3.0.0",
        "docs_url": "/docs",
    }


app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(scooters_router, prefix="/api/scooters", tags=["Scooters"])
app.include_router(rentals_router, prefix="/api/rentals", tags=["Rentals"])

if __name__ == "__main__":
    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
