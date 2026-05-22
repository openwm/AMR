from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.inbound.router import router as inbound_router
from app.modules.inventory.router import router as inventory_router
from app.modules.outbound.router import router as outbound_router
from app.modules.reporting.router import router as reporting_router

app = FastAPI(
    title="OpenWM API",
    version="0.1.0",
    description="Warehouse Management System — demo platform.",
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


app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
app.include_router(inbound_router, prefix="/api/inbound", tags=["inbound"])
app.include_router(outbound_router, prefix="/api/outbound", tags=["outbound"])
app.include_router(reporting_router, prefix="/api/reporting", tags=["reporting"])
