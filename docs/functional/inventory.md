# Inventory Module

## Purpose

The Inventory module is the **source of truth for what stock OpenWM is tracking, and where it lives**. Every other module reads from it (reporting, picking, dashboards) or writes to it (inbound receipts, outbound shipments). If a warehouse only ran this module, it would already have a substantial improvement over spreadsheet-based stock management: real-time stock-on-hand by location, with a full audit trail.

## Key capabilities

- **Product catalog** — SKU, name, unit of measure, barcode, category, unit cost, low-stock threshold
- **Location hierarchy** — zones, aisles, racks, bins; typed as STORAGE, RECEIVING, SHIPPING, or QUARANTINE; flagged pickable / non-pickable
- **Stock on hand** — quantities tracked per (product × location × lot/batch), so the same SKU can live in multiple places with different expiry dates
- **Movement ledger** — every change to stock is recorded as an immutable `StockMovement` row (RECEIPT, PUTAWAY, PICK, SHIP, ADJUSTMENT, TRANSFER). The on-hand quantity at any moment is derivable from the ledger; this is the audit trail customers expect
- **Manual adjustments** — operators can create one-off movements with a note (e.g., damage write-off, cycle count correction)

## Typical workflow

1. **Set up the catalog** — define products and storage locations (one-time setup, or imported from an existing system)
2. **Stock flows in** via the Inbound module — receipts create `RECEIPT` movements; put-away creates `PUTAWAY` movements at the destination bin
3. **Stock flows out** via the Outbound module — picks create `PICK` (negative) movements; shipments create `SHIP` movements
4. **Operators monitor** the **Stock** view to see current on-hand and the **Movements** view as a live audit log
5. **Discrepancies** are handled with a manual `ADJUSTMENT` movement carrying a free-text note for traceability

## Data captured

| Entity         | What it represents                                                           |
|----------------|------------------------------------------------------------------------------|
| Product        | A SKU the warehouse handles. Carries name, UoM, barcode, category, cost     |
| Location       | A physical spot stock can sit. Zone / aisle / rack / bin, with a type        |
| StockItem      | Current quantity of one product at one location for one lot                  |
| StockMovement  | An audit-grade record of any change to stock. Immutable                      |

## Integration points

- **Inbound module** writes `RECEIPT` and `PUTAWAY` movements when goods arrive
- **Outbound module** writes `PICK` and `SHIP` movements when orders ship
- **Reporting module** reads from `StockMovement` and `StockItem` to produce KPIs, throughput charts, and low-stock alerts

## Roles

| Action                             | Operator | Admin |
|------------------------------------|:--------:|:-----:|
| View products, locations, stock    | ✔        | ✔     |
| Create/edit products & locations   |          | ✔     |
| Create manual stock adjustment     | ✔ (note required) | ✔ |
| Delete products / locations        |          | ✔     |

_(Role enforcement is added in the Auth phase.)_
