from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.outbound import schemas, service
from app.modules.outbound.models import SalesOrder, Shipment, ShipmentLine, SOLine

router = APIRouter()


# ---------- Sales orders ----------

@router.get("/sales-orders", response_model=list[schemas.SORead])
def list_sales_orders(
    db: Session = Depends(get_db),
    status_filter: str | None = None,
) -> list[SalesOrder]:
    stmt = select(SalesOrder)
    if status_filter:
        stmt = stmt.where(SalesOrder.status == status_filter)
    stmt = stmt.order_by(desc(SalesOrder.created_at))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/sales-orders", response_model=schemas.SORead, status_code=status.HTTP_201_CREATED
)
def create_sales_order(payload: schemas.SOCreate, db: Session = Depends(get_db)):
    if db.execute(
        select(SalesOrder).where(SalesOrder.reference == payload.reference)
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="SO reference already exists")

    so = SalesOrder(
        reference=payload.reference,
        customer=payload.customer,
        requested_date=payload.requested_date,
        notes=payload.notes,
        status="OPEN",
    )
    for ln in payload.lines:
        so.lines.append(SOLine(product_id=ln.product_id, qty_ordered=ln.qty_ordered))
    db.add(so)
    db.commit()
    db.refresh(so)
    return so


@router.get("/sales-orders/{so_id}", response_model=schemas.SORead)
def get_sales_order(so_id: int, db: Session = Depends(get_db)):
    so = db.get(SalesOrder, so_id)
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return so


# ---------- Shipments ----------

@router.get("/shipments", response_model=list[schemas.ShipmentRead])
def list_shipments(
    db: Session = Depends(get_db),
    so_id: int | None = None,
) -> list[Shipment]:
    stmt = select(Shipment)
    if so_id:
        stmt = stmt.where(Shipment.so_id == so_id)
    stmt = stmt.order_by(desc(Shipment.created_at))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/shipments", response_model=schemas.ShipmentRead, status_code=status.HTTP_201_CREATED
)
def create_shipment(payload: schemas.ShipmentCreate, db: Session = Depends(get_db)):
    if db.execute(
        select(Shipment).where(Shipment.reference == payload.reference)
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Shipment reference already exists")
    if not db.get(SalesOrder, payload.so_id):
        raise HTTPException(status_code=404, detail="Sales order not found")

    shipment = Shipment(
        reference=payload.reference,
        so_id=payload.so_id,
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
        notes=payload.notes,
    )
    for ln in payload.lines:
        shipment.lines.append(
            ShipmentLine(
                so_line_id=ln.so_line_id,
                product_id=ln.product_id,
                location_id=ln.location_id,
                quantity=ln.quantity,
                lot_number=ln.lot_number,
            )
        )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/shipments/{shipment_id}", response_model=schemas.ShipmentRead)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return s


@router.post("/shipments/{shipment_id}/ship", response_model=schemas.ShipmentRead)
def ship_shipment(shipment_id: int, db: Session = Depends(get_db)):
    s = db.get(Shipment, shipment_id)
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    try:
        service.ship(db, s)
        db.commit()
        db.refresh(s)
        return s
    except service.OutboundError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
