from __future__ import annotations

from pydantic import BaseModel


class Kpis(BaseModel):
    product_count: int
    location_count: int
    stock_value: float
    units_on_hand: int
    open_purchase_orders: int
    open_sales_orders: int
    low_stock_products: int


class StockByZone(BaseModel):
    zone: str
    units: int


class ThroughputDay(BaseModel):
    day: str
    inbound: int
    outbound: int


class TopMover(BaseModel):
    sku: str
    name: str
    units_moved: int


class LowStockProduct(BaseModel):
    sku: str
    name: str
    min_stock: int
    on_hand: int


class ActivityEvent(BaseModel):
    kind: str
    reference: str
    status: str
    at: str
