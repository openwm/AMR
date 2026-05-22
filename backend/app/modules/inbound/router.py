from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.inbound import schemas, service
from app.modules.inbound.models import POLine, PurchaseOrder, Receipt, ReceiptLine

router = APIRouter()


# ---------- Purchase orders ----------

@router.get("/purchase-orders", response_model=list[schemas.PORead])
def list_purchase_orders(
    db: Session = Depends(get_db),
    status_filter: str | None = None,
) -> list[PurchaseOrder]:
    stmt = select(PurchaseOrder)
    if status_filter:
        stmt = stmt.where(PurchaseOrder.status == status_filter)
    stmt = stmt.order_by(desc(PurchaseOrder.created_at))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/purchase-orders", response_model=schemas.PORead, status_code=status.HTTP_201_CREATED
)
def create_purchase_order(payload: schemas.POCreate, db: Session = Depends(get_db)):
    if db.execute(
        select(PurchaseOrder).where(PurchaseOrder.reference == payload.reference)
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="PO reference already exists")

    po = PurchaseOrder(
        reference=payload.reference,
        supplier=payload.supplier,
        expected_date=payload.expected_date,
        notes=payload.notes,
        status="OPEN",
    )
    for ln in payload.lines:
        po.lines.append(POLine(product_id=ln.product_id, qty_ordered=ln.qty_ordered))
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


@router.get("/purchase-orders/{po_id}", response_model=schemas.PORead)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.patch("/purchase-orders/{po_id}/status", response_model=schemas.PORead)
def update_po_status(
    po_id: int, payload: schemas.POStatusUpdate, db: Session = Depends(get_db)
):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = payload.status
    db.commit()
    db.refresh(po)
    return po


# ---------- Receipts ----------

@router.get("/receipts", response_model=list[schemas.ReceiptRead])
def list_receipts(
    db: Session = Depends(get_db),
    po_id: int | None = None,
) -> list[Receipt]:
    stmt = select(Receipt)
    if po_id:
        stmt = stmt.where(Receipt.po_id == po_id)
    stmt = stmt.order_by(desc(Receipt.created_at))
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/receipts", response_model=schemas.ReceiptRead, status_code=status.HTTP_201_CREATED
)
def create_receipt(payload: schemas.ReceiptCreate, db: Session = Depends(get_db)):
    if db.execute(
        select(Receipt).where(Receipt.reference == payload.reference)
    ).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Receipt reference already exists")

    receipt = Receipt(reference=payload.reference, po_id=payload.po_id, notes=payload.notes)
    for ln in payload.lines:
        receipt.lines.append(
            ReceiptLine(
                po_line_id=ln.po_line_id,
                product_id=ln.product_id,
                location_id=ln.location_id,
                quantity=ln.quantity,
                lot_number=ln.lot_number,
                expiry_date=ln.expiry_date,
            )
        )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


@router.get("/receipts/{receipt_id}", response_model=schemas.ReceiptRead)
def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return r


@router.post("/receipts/{receipt_id}/complete", response_model=schemas.ReceiptRead)
def complete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    try:
        service.complete_receipt(db, r)
        db.commit()
        db.refresh(r)
        return r
    except service.InboundError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
