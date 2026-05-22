# Outbound Module

## Purpose

The Outbound module owns the **goods-out** side of the warehouse: customer sales orders, picking the right items from the right locations, and shipping them out the door. It is typically the most operationally intensive part of a WMS — every minute spent here directly affects fulfillment SLAs — and it is the most compelling part of a demo because customers can immediately see the dollars-and-cents impact of faster, more accurate picking.

## Key capabilities

- **Sales orders** — capture what a customer ordered: reference, customer name, requested date, line-level SKUs and quantities
- **Stock-aware picking** — when shipping, operators see the live locations that hold the SKU and their current on-hand quantity, so they always pick from a real bin
- **Multi-location picks** — a single order can be picked across multiple locations and lots in one shipment
- **Partial shipments** — orders can ship in stages; the system tracks `qty_ordered` vs. `qty_shipped` per line and auto-transitions OPEN → PARTIAL → SHIPPED
- **Carrier & tracking capture** — every shipment records the carrier and tracking number, ready to be surfaced to customer service or shared with the customer
- **Audit trail** — every shipment writes immutable `PICK` movements to the inventory ledger with a back-reference to the shipment ID

## Typical workflow

1. **Sales creates an SO** with the customer, requested ship date, and the SKUs/quantities ordered
2. **Warehouse operator opens the order** and clicks **Pick & ship**
3. **The system pre-fills** the picks from the location with the highest available stock for each line; the operator can switch locations or split picks
4. **One click ships** — backend creates a Shipment and applies `PICK` movements that decrement stock from the chosen locations
5. **Order status auto-updates** to PARTIAL (if only some lines shipped) or SHIPPED (if all complete)
6. **Stock disappears** from the Inventory view in real time; the dashboard's outbound-throughput KPI ticks up

## Data captured

| Entity         | What it represents                                                     |
|----------------|------------------------------------------------------------------------|
| SalesOrder     | A customer commitment — customer, requested date, status               |
| SOLine         | A specific SKU and quantity on an SO; tracks ordered vs. shipped       |
| Shipment       | A single act of sending goods out (one truck, one parcel)              |
| ShipmentLine   | A line on a shipment with source location, quantity, lot               |

## Integration points

- **Inventory module** is updated when a shipment ships — `PICK` movements decrement stock at the chosen source location
- **Reporting module** reads shipment history to power outbound-throughput KPIs, top-movers analysis, and order fulfilment metrics

## Roles

| Action                                  | Operator | Admin |
|-----------------------------------------|:--------:|:-----:|
| View sales orders & shipments           | ✔        | ✔     |
| Create sales order                      |          | ✔     |
| Pick & ship against an SO               | ✔        | ✔     |
| Cancel an SO / edit after creation      |          | ✔     |

_(Role enforcement is added in the Auth phase.)_
