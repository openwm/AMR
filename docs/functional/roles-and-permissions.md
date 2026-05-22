# Roles & Permissions

OpenWM ships with two demo roles. They map to how warehouse teams are typically structured: people who **operate the warehouse day-to-day** and people who **configure the system and place orders**.

> _For the v1 demo, role enforcement is descriptive — the API does not gate by role yet. Adding JWT-based authentication and role guards is a follow-up phase. Until then, the matrix below describes the **intended** permissions._

## Roles

| Role      | Who it represents                                                       |
|-----------|-------------------------------------------------------------------------|
| Operator  | Warehouse floor staff — receivers, pickers, shippers                    |
| Admin     | Inventory managers, buyers, salespeople, IT — anyone configuring the WMS |

## Permission matrix

| Capability                                  | Operator | Admin |
|---------------------------------------------|:--------:|:-----:|
| View dashboard & all read-only reports      | ✔        | ✔     |
| **Inventory**                               |          |       |
| Browse products / locations / stock         | ✔        | ✔     |
| Create or edit products                     |          | ✔     |
| Create or edit locations                    |          | ✔     |
| Manual stock adjustment (with reason note)  | ✔        | ✔     |
| Delete products or locations                |          | ✔     |
| **Inbound**                                 |          |       |
| Browse purchase orders & receipts           | ✔        | ✔     |
| Create / edit purchase orders               |          | ✔     |
| Receive against a PO                        | ✔        | ✔     |
| Close or cancel a PO                        |          | ✔     |
| **Outbound**                                |          |       |
| Browse sales orders & shipments             | ✔        | ✔     |
| Create / edit sales orders                  |          | ✔     |
| Pick & ship                                 | ✔        | ✔     |
| Cancel a sales order                        |          | ✔     |

## Default demo users

When the auth phase ships, the seed will create two users:

| Username  | Password   | Role     |
|-----------|------------|----------|
| `admin`   | `admin`    | Admin    |
| `operator`| `operator` | Operator |

Both must be changed before any production-style deployment — see the deployment manual.
