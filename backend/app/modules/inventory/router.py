from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.modules.inventory import schemas, service
from app.modules.inventory.models import Location, Product, StockItem, StockMovement

router = APIRouter()


# ---------- Products ----------

@router.get("/products", response_model=list[schemas.ProductRead])
def list_products(
    db: Session = Depends(get_db),
    search: str | None = Query(None, description="Search by SKU or name (case-insensitive)"),
    category: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[Product]:
    stmt = select(Product)
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            (Product.sku.ilike(like)) | (Product.name.ilike(like))
        )
    if category:
        stmt = stmt.where(Product.category == category)
    stmt = stmt.order_by(Product.sku).offset(offset).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.post("/products", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)) -> Product:
    existing = db.execute(select(Product).where(Product.sku == payload.sku)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{payload.sku}' already exists")
    p = Product(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/products/{product_id}", response_model=schemas.ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@router.patch("/products/{product_id}", response_model=schemas.ProductRead)
def update_product(
    product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)
) -> Product:
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()


# ---------- Locations ----------

@router.get("/locations", response_model=list[schemas.LocationRead])
def list_locations(
    db: Session = Depends(get_db),
    zone: str | None = None,
    type: str | None = None,
) -> list[Location]:
    stmt = select(Location)
    if zone:
        stmt = stmt.where(Location.zone == zone)
    if type:
        stmt = stmt.where(Location.type == type)
    stmt = stmt.order_by(Location.code)
    return list(db.execute(stmt).scalars().all())


@router.post(
    "/locations", response_model=schemas.LocationRead, status_code=status.HTTP_201_CREATED
)
def create_location(payload: schemas.LocationCreate, db: Session = Depends(get_db)) -> Location:
    existing = db.execute(
        select(Location).where(Location.code == payload.code)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Location code '{payload.code}' exists")
    loc = Location(**payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.get("/locations/{location_id}", response_model=schemas.LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)) -> Location:
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@router.patch("/locations/{location_id}", response_model=schemas.LocationRead)
def update_location(
    location_id: int, payload: schemas.LocationUpdate, db: Session = Depends(get_db)
) -> Location:
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loc, field, value)
    db.commit()
    db.refresh(loc)
    return loc


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(loc)
    db.commit()


# ---------- Stock on hand ----------

@router.get("/stock", response_model=list[schemas.StockItemRead])
def list_stock(
    db: Session = Depends(get_db),
    product_id: int | None = None,
    location_id: int | None = None,
    only_with_qty: bool = True,
) -> list[schemas.StockItemRead]:
    stmt = select(StockItem)
    if product_id:
        stmt = stmt.where(StockItem.product_id == product_id)
    if location_id:
        stmt = stmt.where(StockItem.location_id == location_id)
    if only_with_qty:
        stmt = stmt.where(StockItem.quantity > 0)
    stmt = stmt.order_by(StockItem.id)
    results = []
    for s in db.execute(stmt).scalars().all():
        results.append(
            schemas.StockItemRead(
                id=s.id,
                product_id=s.product_id,
                location_id=s.location_id,
                quantity=s.quantity,
                lot_number=s.lot_number,
                expiry_date=s.expiry_date,
                updated_at=s.updated_at,
                product_sku=s.product.sku if s.product else None,
                product_name=s.product.name if s.product else None,
                location_code=s.location.code if s.location else None,
            )
        )
    return results


# ---------- Movements ----------

@router.get("/movements", response_model=list[schemas.MovementRead])
def list_movements(
    db: Session = Depends(get_db),
    product_id: int | None = None,
    location_id: int | None = None,
    movement_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[schemas.MovementRead]:
    stmt = select(StockMovement)
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    if location_id:
        stmt = stmt.where(StockMovement.location_id == location_id)
    if movement_type:
        stmt = stmt.where(StockMovement.movement_type == movement_type)
    stmt = stmt.order_by(desc(StockMovement.created_at)).offset(offset).limit(limit)
    results = []
    for m in db.execute(stmt).scalars().all():
        results.append(
            schemas.MovementRead(
                id=m.id,
                product_id=m.product_id,
                location_id=m.location_id,
                quantity=m.quantity,
                movement_type=m.movement_type,
                reference_type=m.reference_type,
                reference_id=m.reference_id,
                lot_number=m.lot_number,
                note=m.note,
                created_at=m.created_at,
                product_sku=m.product.sku if m.product else None,
                product_name=m.product.name if m.product else None,
                location_code=m.location.code if m.location else None,
            )
        )
    return results


@router.post(
    "/movements", response_model=schemas.MovementRead, status_code=status.HTTP_201_CREATED
)
def create_movement(payload: schemas.MovementCreate, db: Session = Depends(get_db)):
    try:
        m = service.apply_movement(
            db,
            product_id=payload.product_id,
            location_id=payload.location_id,
            quantity=payload.quantity,
            movement_type=payload.movement_type,
            reference_type=payload.reference_type or "ADJUSTMENT",
            reference_id=payload.reference_id,
            lot_number=payload.lot_number,
            note=payload.note,
        )
        db.commit()
        db.refresh(m)
        return schemas.MovementRead.model_validate(m)
    except service.InventoryError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
