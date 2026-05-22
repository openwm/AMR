"""Idempotent demo data seeder.

Run via `python -m app.seed.seed` (the API container runs this automatically
on start when SEED_DEMO_DATA=true). Safe to re-run — exits early if the
catalog has already been seeded.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.inbound.models import POLine, PurchaseOrder, Receipt, ReceiptLine
from app.modules.inbound.service import complete_receipt
from app.modules.inventory.models import Location, Product, StockItem
from app.modules.outbound.models import SalesOrder, Shipment, ShipmentLine, SOLine
from app.modules.outbound.service import ship

# Seed-data definitions ----------------------------------------------------

CATEGORIES = ["Electronics", "Apparel", "Hardware", "Home", "Food"]

PRODUCT_NAMES: dict[str, list[str]] = {
    "Electronics": [
        "Wireless mouse",
        "Mechanical keyboard",
        "USB-C cable 2m",
        "Bluetooth headphones",
        "Webcam 1080p",
        "Power bank 20000mAh",
        "HDMI cable 3m",
        "Laptop stand",
        "Desk lamp LED",
        "Portable speaker",
    ],
    "Apparel": [
        "Cotton t-shirt M",
        "Cotton t-shirt L",
        "Hoodie M",
        "Hoodie L",
        "Jeans 32x32",
        "Jeans 34x32",
        "Wool socks",
        "Baseball cap",
        "Leather belt",
        "Rain jacket",
    ],
    "Hardware": [
        "Screwdriver set",
        "Cordless drill",
        "Hammer 16oz",
        "Measuring tape 5m",
        "Adjustable wrench",
        "Utility knife",
        "Hex key set",
        "Wood saw",
        "Pliers 8\"",
        "Stud finder",
    ],
    "Home": [
        "Coffee mug",
        "Stainless water bottle",
        "Bath towel set",
        "Pillow standard",
        "Throw blanket",
        "Cutting board",
        "Knife set",
        "Picture frame A4",
        "Desk organizer",
        "Floor lamp",
    ],
    "Food": [
        "Coffee beans 1kg",
        "Olive oil 500ml",
        "Pasta 500g",
        "Canned tomatoes",
        "Granola 750g",
        "Honey 500g",
        "Tea bags x100",
        "Dark chocolate bar",
        "Rice 1kg",
        "Sea salt 1kg",
    ],
}

ZONES = [("A", "STORAGE"), ("B", "STORAGE"), ("C", "STORAGE")]
SUPPLIERS = ["Acme Supply Co", "Globex Distribution", "Initech Wholesale", "Soylent Imports"]
CUSTOMERS = [
    "Wayne Industries",
    "Stark Logistics",
    "Pied Piper Inc",
    "Hooli Stores",
    "Vandelay Imports",
    "Dunder Mifflin",
]


def _has_seeded(db) -> bool:
    return db.scalar(select(Product).limit(1)) is not None


def _seed_products(db) -> list[Product]:
    products: list[Product] = []
    for category in CATEGORIES:
        for i, name in enumerate(PRODUCT_NAMES[category], start=1):
            sku = f"{category[:3].upper()}-{i:03d}"
            p = Product(
                sku=sku,
                name=name,
                description=f"{name} ({category})",
                uom="EA",
                barcode=f"50{random.randint(10000000, 99999999)}",
                category=category,
                min_stock=random.choice([0, 5, 10, 20]),
                unit_cost=Decimal(str(round(random.uniform(2, 200), 2))),
            )
            db.add(p)
            products.append(p)
    db.flush()
    return products


def _seed_locations(db) -> list[Location]:
    locations: list[Location] = []
    for zone, _ in ZONES:
        for aisle in range(1, 4):
            for rack in range(1, 4):
                code = f"{zone}-{aisle:02d}-{rack:02d}"
                loc = Location(
                    code=code,
                    zone=zone,
                    aisle=f"{aisle:02d}",
                    rack=f"{rack:02d}",
                    type="STORAGE",
                    is_pickable=True,
                )
                db.add(loc)
                locations.append(loc)
    db.add(
        Location(code="DOCK-IN", zone="DOCK", type="RECEIVING", is_pickable=False)
    )
    db.add(
        Location(code="DOCK-OUT", zone="DOCK", type="SHIPPING", is_pickable=False)
    )
    db.flush()
    return locations


def _seed_inbound(db, products: list[Product], storage_locs: list[Location]) -> None:
    """Generate 10 POs over the last ~60 days, with receipts."""
    base = datetime.now(timezone.utc) - timedelta(days=60)
    for i in range(1, 11):
        po_date = base + timedelta(days=i * 5)
        po = PurchaseOrder(
            reference=f"PO-2026-{i:04d}",
            supplier=random.choice(SUPPLIERS),
            status="OPEN",
            expected_date=(po_date + timedelta(days=3)).date(),
            notes=None,
        )
        po.created_at = po_date
        line_products = random.sample(products, k=random.randint(3, 6))
        for prod in line_products:
            po.lines.append(
                POLine(product_id=prod.id, qty_ordered=random.randint(20, 200))
            )
        db.add(po)
        db.flush()

        # ~80% of POs have been fully received
        if i <= 8:
            receipt = Receipt(
                reference=f"R-{po.reference}-01",
                po_id=po.id,
                notes=None,
            )
            receipt.created_at = po_date + timedelta(days=3, hours=random.randint(1, 8))
            for line in po.lines:
                receipt.lines.append(
                    ReceiptLine(
                        po_line_id=line.id,
                        product_id=line.product_id,
                        location_id=random.choice(storage_locs).id,
                        quantity=line.qty_ordered,
                        lot_number=f"LOT-{po_date.strftime('%Y%m')}",
                    )
                )
            db.add(receipt)
            db.flush()
            complete_receipt(db, receipt)


def _seed_outbound(db, products: list[Product]) -> None:
    """Generate 20 SOs, ship ~70% of them."""
    base = datetime.now(timezone.utc) - timedelta(days=45)

    # Snapshot of stock available for shipping. Keyed by stock_item.id so we
    # track availability independently of the live SQLAlchemy quantity (which
    # ship() will decrement via apply_movement).
    stock_rows = db.execute(select(StockItem).where(StockItem.quantity > 0)).scalars().all()
    avail_by_product: dict[int, list[tuple[StockItem, list[int]]]] = {}
    for s in stock_rows:
        # Use a 1-element list to make the int mutable from within the loop
        avail_by_product.setdefault(s.product_id, []).append((s, [s.quantity]))

    for i in range(1, 21):
        so_date = base + timedelta(days=i * 2)
        so = SalesOrder(
            reference=f"SO-2026-{i:04d}",
            customer=random.choice(CUSTOMERS),
            status="OPEN",
            requested_date=(so_date + timedelta(days=2)).date(),
        )
        so.created_at = so_date

        line_products = [
            p
            for p in random.sample(products, k=random.randint(2, 5))
            if avail_by_product.get(p.id)
        ]
        if not line_products:
            db.add(so)
            continue
        for prod in line_products:
            stocks = avail_by_product.get(prod.id, [])
            total_avail = sum(box[0] for _, box in stocks)
            if total_avail <= 0:
                continue
            qty = random.randint(1, max(1, min(20, total_avail // 2)))
            so.lines.append(SOLine(product_id=prod.id, qty_ordered=qty))

        if not so.lines:
            db.add(so)
            continue
        db.add(so)
        db.flush()

        # ~70% shipped
        if i <= 14:
            shipment = Shipment(
                reference=f"S-{so.reference}-01",
                so_id=so.id,
                carrier=random.choice(["FedEx", "UPS", "DHL"]),
                tracking_number=f"TRK{random.randint(10**9, 10**10 - 1)}",
            )
            shipment.created_at = so_date + timedelta(days=1)
            for line in so.lines:
                stocks = avail_by_product.get(line.product_id, [])
                qty_left = line.qty_ordered
                for s, box in stocks:
                    if qty_left <= 0 or box[0] <= 0:
                        continue
                    take = min(qty_left, box[0])
                    shipment.lines.append(
                        ShipmentLine(
                            so_line_id=line.id,
                            product_id=line.product_id,
                            location_id=s.location_id,
                            quantity=take,
                            lot_number=s.lot_number,
                        )
                    )
                    box[0] -= take  # snapshot bookkeeping, doesn't touch ORM state
                    qty_left -= take
            if shipment.lines:
                db.add(shipment)
                db.flush()
                try:
                    ship(db, shipment)
                except Exception:
                    db.rollback()
                    continue


def main() -> None:
    if not settings.SEED_DEMO_DATA:
        print("[seed] SEED_DEMO_DATA disabled — skipping.")
        return

    random.seed(42)  # deterministic demo data
    db = SessionLocal()
    try:
        if _has_seeded(db):
            print("[seed] Database already populated — skipping.")
            return

        print("[seed] Seeding products…")
        products = _seed_products(db)
        print(f"[seed]   {len(products)} products")

        print("[seed] Seeding locations…")
        locations = _seed_locations(db)
        storage_locs = [l for l in locations if l.type == "STORAGE"]
        print(f"[seed]   {len(locations)} locations ({len(storage_locs)} storage)")

        print("[seed] Seeding inbound (POs + receipts)…")
        _seed_inbound(db, products, storage_locs)

        print("[seed] Seeding outbound (SOs + shipments)…")
        _seed_outbound(db, products)

        db.commit()
        print("[seed] Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
