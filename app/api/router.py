from fastapi import APIRouter

from app.api import (
    alerts,
    anomalies,
    dashboard,
    incidents,
    maintenance,
    permits,
    plant_zone,
    response_actions,
    risks,
    sensors,
    workers,
)


api_router = APIRouter()


api_router.include_router(
    sensors.router
)

api_router.include_router(
    risks.router
)

api_router.include_router(
    incidents.router
)

api_router.include_router(
    alerts.router
)
api_router.include_router(
    response_actions.router
)

api_router.include_router(
    anomalies.router
)

api_router.include_router(
    permits.router
)

api_router.include_router(
    maintenance.router
)

api_router.include_router(
    plant_zone.router
)

api_router.include_router(
    workers.router
)
api_router.include_router(
    dashboard.router
)