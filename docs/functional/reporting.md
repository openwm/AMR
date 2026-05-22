# Reporting Module

## Purpose

The Reporting module turns the operational data from Inventory, Inbound, and Outbound into **the management view** of the warehouse — the single screen that an operations manager or executive can glance at and immediately understand throughput, stock health, and any issues that need attention. It is the headline visual in a sales demo: it tells the story of "OpenWM doesn't just process transactions, it gives you visibility."

## Key capabilities

- **Headline KPIs** — total stock value, units on hand, SKU count, locations in use, open purchase and sales orders, low-stock alert count
- **Throughput trend** — daily inbound vs. outbound units for the last 14 days, plotted as a line chart so spikes and drops are immediately visible
- **Stock by zone** — bar chart of physical distribution of inventory across zones
- **Top movers** — the SKUs with the most movement (in or out) over the last 30 days; useful for slotting decisions
- **Low stock alerts** — every product whose on-hand quantity has fallen below its configured `min_stock` threshold
- **Recent activity** — the most recent receipts and shipments, with timestamps; the live operational pulse

## Typical workflow

The Reporting module is **read-only and ambient**. There are no actions to take; it is the first screen an operator or manager opens in the morning and the last one they close at the end of the day.

1. Open the dashboard — it auto-refreshes every 15 seconds (no manual reloads)
2. Scan KPIs for anomalies (low stock count rising, stock value dropping unexpectedly)
3. Click through to the relevant module if an issue is spotted (e.g., a low-stock SKU)

## Data captured

Reporting **owns no tables**. Every metric is computed live from the data captured by Inventory, Inbound, and Outbound — there is no risk of report data drifting out of sync with operational reality.

## Integration points

- Reads `StockItem`, `StockMovement` from Inventory
- Reads `PurchaseOrder`, `Receipt` from Inbound
- Reads `SalesOrder`, `Shipment` from Outbound
- Joins `Product` for low-stock evaluation and naming

## Roles

All roles can view the dashboard. No write actions.

_(Role enforcement is added in the Auth phase.)_
