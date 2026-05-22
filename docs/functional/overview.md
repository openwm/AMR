# OpenWM — Functional Overview

## What OpenWM is

OpenWM is a **warehouse management system** built to demonstrate how modern WMS capabilities can run as a self-contained, dockerized platform — installed in minutes, no SaaS lock-in, no per-seat fees. It manages the lifecycle of physical goods inside a warehouse:

> goods come in → goods sit somewhere → goods go out → and you can see what's happening at any moment.

The system is delivered as four functional modules that map directly to how warehouse teams are organized in practice.

## The four modules

```
                       ┌────────────────────┐
                       │     Reporting      │
                       │  KPIs · dashboards │
                       └─────────┬──────────┘
                                 │ reads
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
   │    Inbound     │──►│   Inventory    │◄──│    Outbound    │
   │  POs · receipts │   │  source of truth│  │ SOs · shipments│
   └────────────────┘   └────────────────┘   └────────────────┘
            writes               │                   writes
                                 ▼
                       Stock movement ledger
                       (immutable audit trail)
```

| Module      | One-line purpose                                                |
|-------------|-----------------------------------------------------------------|
| [Inventory](inventory.md)   | The source of truth — what stock exists, where it lives, complete audit trail |
| [Inbound](inbound.md)       | Purchase orders, receiving, putting stock away                  |
| [Outbound](outbound.md)     | Sales orders, picking from stock, shipping to customers         |
| [Reporting](reporting.md)   | Live KPIs and dashboards aggregating all of the above           |

Every state change — a receipt, a pick, a shipment, a manual adjustment — produces an immutable row in the `StockMovement` ledger. That ledger is what gives OpenWM its audit-grade traceability: you can always answer the question "where did this stock come from and where did it go?".

## Glossary

| Term            | Meaning                                                                                            |
|-----------------|----------------------------------------------------------------------------------------------------|
| **SKU**         | Stock Keeping Unit — a unique identifier for a product variant                                     |
| **UoM**         | Unit of Measure — how a product is counted (each, kilogram, litre, …)                              |
| **Location**    | A physical spot stock can sit; addressed as Zone-Aisle-Rack-Bin                                    |
| **Lot / Batch** | An identifier that groups stock produced or received together — used for expiry & recall handling   |
| **PO**          | Purchase Order — a commitment to buy goods from a supplier                                         |
| **Receipt**     | The act of physically receiving goods against a PO                                                 |
| **Put-away**    | Moving received goods from the receiving dock to their storage location                            |
| **SO**          | Sales Order — a customer order to be fulfilled                                                     |
| **Pick**        | Removing goods from a storage location to fulfill an order                                         |
| **Shipment**    | A single act of sending goods out to a customer (one truck, one parcel)                            |
| **Movement**    | An audit ledger entry for any change in stock: RECEIPT, PUTAWAY, PICK, SHIP, ADJUSTMENT, TRANSFER  |

## Who uses it

OpenWM is designed around two day-to-day roles plus a manager view:

- **Operator** — receives goods, picks orders, runs the daily transactional flow
- **Admin** — sets up the catalog, creates POs and SOs, manages users and configuration
- **Manager** (any role) — reads the dashboard for visibility

See [roles-and-permissions.md](roles-and-permissions.md) for the per-action permission matrix.
