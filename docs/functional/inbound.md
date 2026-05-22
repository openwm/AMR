# Inbound Module

## Purpose

The Inbound module covers everything that happens when **goods arrive at the warehouse** — from the supplier shipping the order, to operators physically receiving cartons, to stock being put away into its storage location. It converts external supply (purchase orders, supplier deliveries) into trusted on-hand stock that Outbound can pick from.

## Key capabilities

- **Purchase orders** — capture what was ordered from each supplier, with line-level expected quantities and a reference / expected delivery date
- **Receiving** — record what physically arrived: quantity per SKU, the storage location it goes to, and (optionally) the lot/batch number and expiry date
- **Partial receipts** — a single PO can be received over multiple visits; the system tracks `qty_ordered` vs. `qty_received` per line and surfaces the remaining quantity
- **Automatic status progression** — PO status moves DRAFT → OPEN → PARTIAL → RECEIVED based on receipt completion, without manual updates
- **Audit trail** — every completed receipt writes immutable `RECEIPT` movements to the inventory ledger, tying physical activity back to source documents

## Typical workflow

1. **Buyer creates a PO** with a supplier name, expected date, and lines (SKU + quantity ordered)
2. **Truck arrives** — operator opens the PO, clicks **Receive**, and confirms the quantity, destination location, and lot number for each line
3. **Stock appears** in the Inventory module immediately; the PO line shows the new `received` total and any remaining quantity
4. If the supplier ships in multiple deliveries, additional receipts can be added against the same PO until it is fully received
5. The PO is automatically marked **RECEIVED** when all lines are complete, or **PARTIAL** while still in progress

## Data captured

| Entity         | What it represents                                                     |
|----------------|------------------------------------------------------------------------|
| PurchaseOrder  | A commitment to buy something — supplier, expected date, status        |
| POLine         | A specific SKU and quantity on a PO; tracks ordered vs. received        |
| Receipt        | A single act of receiving goods (one truck, one drop-off)              |
| ReceiptLine    | Quantity received against a PO line, with destination location + lot   |

## Integration points

- **Inventory module** is updated when a receipt is completed — `RECEIPT` movements increase on-hand stock at the chosen location
- **Reporting module** reads receipt history to power inbound-throughput KPIs (e.g., receipts/day, units received last 7 days)

## Roles

| Action                                  | Operator | Admin |
|-----------------------------------------|:--------:|:-----:|
| View purchase orders & receipts         | ✔        | ✔     |
| Create purchase order                   |          | ✔     |
| Receive against a purchase order        | ✔        | ✔     |
| Edit/close a purchase order             |          | ✔     |

_(Role enforcement is added in the Auth phase.)_
