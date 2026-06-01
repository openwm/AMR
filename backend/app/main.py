from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.systems.devices.router import router as devices_router
from app.systems.equipment.router import router as equipment_router
from app.systems.wcs.router import router as wcs_router
from app.systems.wcs.service import seed_stations
from app.systems.wms.inbound.router import router as inbound_router
from app.systems.wms.inventory.router import router as inventory_router
from app.systems.wms.outbound.router import router as outbound_router
from app.systems.wms.planning.router import router as planning_router
from app.systems.wms.reporting.router import router as reporting_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_stations()
    yield


app = FastAPI(
    title="OpenWM API",
    version="0.1.0",
    description="Warehouse Management System — demo platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(inventory_router, prefix="/api/wms/inventory", tags=["wms/inventory"])
app.include_router(inbound_router, prefix="/api/wms/inbound", tags=["wms/inbound"])
app.include_router(outbound_router, prefix="/api/wms/outbound", tags=["wms/outbound"])
app.include_router(planning_router, prefix="/api/wms/planning", tags=["wms/planning"])
app.include_router(reporting_router, prefix="/api/wms/reporting", tags=["wms/reporting"])
app.include_router(wcs_router, prefix="/api/wcs", tags=["wcs"])
app.include_router(equipment_router, prefix="/api/equipment", tags=["equipment"])
app.include_router(devices_router, prefix="/api/devices", tags=["devices"])
