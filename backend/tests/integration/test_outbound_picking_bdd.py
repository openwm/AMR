"""
Gherkin integration test: full outbound picking flow with AMR simulation.

Prerequisites:
    docker compose up

Run (manual — operator confirms picks via the picking station UI, DEFAULT):
    pytest backend/tests/integration/test_outbound_picking_bdd.py -v -s

Run (automated — no UI interaction required):
    pytest backend/tests/integration/test_outbound_picking_bdd.py -v -s --auto
"""

import time

import pytest
from pytest_bdd import given, scenarios, then, when
from pytest_bdd import parsers

from tests.integration.conftest import (
    AMR_SIM_BASE,
    clear_wcs_tasks,
    ensure_amr_fleet,
    force_close_test_orders,
)

scenarios("features/outbound_picking.feature")

PICKING_UI_BASE = "http://localhost:5173"

# ── Background ────────────────────────────────────────────────────────────────

@given("the warehouse system is reset")
def reset_system(http_client, amr_sim_client, ctx):
    """
    Full system reset before each scenario:
      - Exception all non-terminal WCS tasks (clears station queues)
      - Lift planning capacity limits so prior stuck test orders don't block release
      - Ensure at least 2 AMRs are registered in the simulator fleet
    """
    # 1. Force-ship any leftover test orders so they leave ACTIVE/PICKING state.
    #    This must run before clear_wcs_tasks, because the stock PATCH route
    #    requires the order to still be in PICKING/ACTIVE.
    closed = force_close_test_orders(http_client)
    # 2. Exception all remaining WCS tasks (incl. tasks from non-test orders).
    clear_wcs_tasks(http_client)
    # 3. Lift planning limits so a single lingering non-test PICKING order can't
    #    block the run (belt-and-suspenders on top of step 1).
    http_client.patch(
        "/api/wms/planning/config",
        json={"max_active_orders": 100, "max_picking_orders": 100},
    )
    ensure_amr_fleet(amr_sim_client, min_count=2)
    ctx.clear()
    amrs = amr_sim_client.get("/amrs").json()
    msg = f"force-closed {closed} stuck order(s), " if closed else ""
    print(f"\n[reset] {msg}WCS cleared, capacity limits lifted, {len(amrs)} AMR(s) in fleet")


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse("inventory is seeded for {count:d} products in warehouse locations"))
def seed_inventory(http_client, ctx, count):
    """
    Ensure exactly `count` products each have at least 1 AVAILABLE unit in a
    storage location.  Products that already have stock are used as-is; any
    that are out of stock get a new receipt created and completed via the
    inbound API so the test never fails due to prior runs draining inventory.
    """
    products = http_client.get("/api/wms/inventory/products", params={"limit": 50}).json()
    assert products, "No products in catalog — run database seed first"

    # Pick a stable storage location for emergency receipts
    locs = http_client.get("/api/wms/inventory/locations", params={"type": "STORAGE"}).json()
    assert locs, "No storage locations in database"
    loc_id = locs[0]["id"]

    selected: list[int] = []
    for product in products:
        if len(selected) >= count:
            break
        pid = product["id"]
        stock = http_client.get("/api/wms/inventory/stock", params={"product_id": pid}).json()
        if any(s["status"] == "AVAILABLE" and s["quantity"] > 0 for s in stock):
            selected.append(pid)
            continue
        # Product is out of AVAILABLE stock — receive 20 units into the warehouse.
        # Use a unique lot_number so apply_movement creates a fresh AVAILABLE
        # StockItem rather than incrementing a leftover ALLOCATED one at the
        # same (product, location, lot) key.
        lot = f"BDD-{int(time.time())}-{pid}"
        ref = f"BDD-RECEIPT-{lot}"
        r = http_client.post(
            "/api/wms/inbound/receipts",
            json={"reference": ref, "lines": [{"product_id": pid, "location_id": loc_id, "quantity": 20, "lot_number": lot}]},
        )
        if r.status_code != 201:
            continue
        comp = http_client.post(f"/api/wms/inbound/receipts/{r.json()['id']}/complete")
        if comp.status_code == 200:
            selected.append(pid)

    if len(selected) < count:
        pytest.fail(f"Could only source {len(selected)} product(s) with available stock, needed {count}")

    ctx["product_ids"] = selected[:count]
    print(f"[step] Inventory seeded for products: {ctx['product_ids']}")


# ── When ──────────────────────────────────────────────────────────────────────

@when("an outbound order is submitted with those products")
def submit_order(http_client, ctx):
    ref = f"BDD-PICK-{int(time.time())}"
    resp = http_client.post(
        "/api/wms/outbound/sales-orders",
        json={
            "reference": ref,
            "customer": "BDD Integration Test",
            "lines": [{"product_id": pid, "qty_ordered": 1} for pid in ctx["product_ids"]],
        },
    )
    assert resp.status_code == 201, resp.text
    so = resp.json()
    ctx["so_id"] = so["id"]
    ctx["so_ref"] = ref
    ctx["line_ids"] = [ln["id"] for ln in so["lines"]]
    print(f"[step] Order created — id={ctx['so_id']} ref={ref} lines={ctx['line_ids']}")


@when("planning allocates the inventory")
def run_planning(http_client, ctx):
    resp = http_client.post("/api/wms/planning/run")
    assert resp.status_code == 200, resp.text
    print(f"[step] Planning: {resp.json()}")


@when("the order is released to the warehouse control system")
def release_to_wcs(http_client, ctx):
    resp = http_client.post("/api/wms/planning/release")
    assert resp.status_code == 200, resp.text
    print(f"[step] WCS release: {resp.json()}")

    # Locate the WCS pick task for every SO line (tasks may land on different stations)
    so_id = ctx["so_id"]
    line_ids = ctx["line_ids"]
    tasks: dict[str, dict] = {}  # task_id → full task dict (includes station_id, product_id)

    for _ in range(20):
        stations = http_client.get("/api/wcs/stations").json()
        for s in stations:
            queue = http_client.get(f"/api/wcs/stations/{s['station_id']}/queue").json()
            for t in queue.get("tasks", []):
                if t["order_id"] == so_id and t["order_line_id"] in line_ids:
                    tasks[t["id"]] = t
        if len(tasks) == len(line_ids):
            break
        time.sleep(0.5)

    assert len(tasks) == len(line_ids), (
        f"Expected {len(line_ids)} WCS task(s) for SO {so_id}, found {len(tasks)}"
    )
    ctx["tasks"] = tasks
    stations_used = {t["station_id"] for t in tasks.values()}
    print(f"[step] {len(tasks)} task(s) queued at station(s): {stations_used}")


@when("an AMR travels to each inventory location to collect the stock")
def amr_collects_inventory(http_client, amr_sim_client, ctx):
    """
    For each pick task, find the ALLOCATED stock location of the product,
    dispatch the nearest available AMR to that location, and wait until
    every AMR has arrived (simulating inventory pickup).
    """
    tasks: dict[str, dict] = ctx["tasks"]

    # Build product_id → inventory location_code from ALLOCATED stock items
    pid_to_location: dict[int, str] = {}
    for task_data in tasks.values():
        pid = task_data["product_id"]
        if pid in pid_to_location:
            continue
        stock = http_client.get(
            "/api/wms/inventory/stock", params={"product_id": pid}
        ).json()
        allocated = [
            s for s in stock
            if s["status"] == "ALLOCATED" and s["quantity"] > 0 and s.get("location_code")
        ]
        if not allocated:
            pytest.fail(f"No ALLOCATED stock with a location found for product {pid}")
        pid_to_location[pid] = allocated[0]["location_code"]

    print(f"[step] Inventory locations: { {p: l for p, l in pid_to_location.items()} }")

    # Dispatch one AMR per task to its inventory location.
    # Tasks are processed sequentially so each dispatch uses a different AMR
    # (the previous one is already traveling when the next call goes out).
    task_amr: dict[str, str] = {}  # task_id → amr_id

    for task_id, task_data in tasks.items():
        pid = task_data["product_id"]
        loc_code = pid_to_location[pid]

        # Wait for an available AMR (idle or at_location) then dispatch
        dispatched_id: str | None = None
        for _ in range(60):  # up to 30 s
            resp = amr_sim_client.post("/dispatch", json={"location_code": loc_code})
            if resp.status_code == 200:
                dispatched_id = resp.json()["id"]
                break
            time.sleep(0.5)  # 503 = no AMR free yet

        if dispatched_id is None:
            pytest.fail(f"No AMR became available to collect from {loc_code}")

        task_amr[task_id] = dispatched_id
        print(f"[step] AMR {dispatched_id} dispatched to inventory location {loc_code}")

    # Wait for every dispatched AMR to reach its inventory location
    for task_id, amr_id in task_amr.items():
        loc_code = pid_to_location[tasks[task_id]["product_id"]]
        for _ in range(120):  # up to 60 s
            amrs = amr_sim_client.get("/amrs").json()
            amr = next((a for a in amrs if a["id"] == amr_id), None)
            if amr and amr["status"] == "at_location" and amr.get("target_location") == loc_code:
                print(f"[step] AMR {amr_id} arrived at inventory location {loc_code} — stock collected")
                break
            time.sleep(0.5)
        else:
            pytest.fail(f"AMR {amr_id} did not reach inventory location {loc_code} within 60 s")

    ctx["task_amr"] = task_amr
    ctx["pid_to_location"] = pid_to_location


@when("the AMR delivers the stock to the pick station")
def amr_delivers_to_station(http_client, amr_sim_client, ctx):
    """
    Dispatch each AMR from its inventory location to the pick station assigned
    to its task, then wait for physical arrival. Also verifies the WCS task
    is at_dock (ready for the operator).
    """
    tasks: dict[str, dict] = ctx["tasks"]
    task_amr: dict[str, str] = ctx["task_amr"]

    # Dispatch every AMR towards its pick station
    for task_id, task_data in tasks.items():
        amr_id = task_amr[task_id]
        station_id = task_data["station_id"]
        resp = amr_sim_client.post(
            f"/amrs/{amr_id}/dispatch", json={"location_code": station_id}
        )
        assert resp.status_code == 200, f"AMR dispatch to {station_id} failed: {resp.text}"
        print(f"[step] AMR {amr_id} dispatched from inventory to pick station {station_id}")

    # Wait for every AMR to arrive at its pick station
    for task_id, amr_id in task_amr.items():
        station_id = tasks[task_id]["station_id"]
        for _ in range(120):  # up to 60 s
            amrs = amr_sim_client.get("/amrs").json()
            amr = next((a for a in amrs if a["id"] == amr_id), None)
            if amr and amr["status"] == "at_location" and amr.get("target_location") == station_id:
                print(f"[step] AMR {amr_id} arrived at pick station {station_id} — inventory delivered")
                break
            time.sleep(0.5)
        else:
            pytest.fail(f"AMR {amr_id} did not reach pick station {station_id} within 60 s")

    # Verify each WCS task exists in the queue and is not excepted.
    # A task may be in "queued" (not yet at_dock) if another order's task holds
    # the at_dock slot — that is normal and handled in pick_all_items.
    for task_id, task_data in tasks.items():
        station_id = task_data["station_id"]
        for _ in range(20):
            queue = http_client.get(f"/api/wcs/stations/{station_id}/queue").json()
            t = next((x for x in queue.get("tasks", []) if x["id"] == task_id), None)
            if t and t["status"] != "exception":
                print(f"[step] WCS task {task_id} at {station_id} — status: {t['status']}")
                break
            time.sleep(0.5)
        else:
            pytest.fail(f"WCS task {task_id} not found (or excepted) at {station_id}")


@when("the operator picks all items at the picking station")
def pick_all_items(http_client, ctx, manual):
    tasks: dict[str, dict] = ctx["tasks"]
    so_ref: str = ctx["so_ref"]

    if manual:
        unique_stations = sorted({t["station_id"] for t in tasks.values()})
        print(f"\n[MANUAL] Open the picking station UI:")
        for sid in unique_stations:
            print(f"[MANUAL]   {PICKING_UI_BASE}/devices/picking/{sid}")
        print(f"[MANUAL] Confirm {len(tasks)} pick(s) for order {so_ref} — click 'Confirm Pick' for each.\n")

        # Poll the WMS order status — it transitions to SHIPPED only after all
        # WCS callbacks have fired (one per completed pick), which is the true
        # signal that every pick was confirmed.
        so_id = ctx["so_id"]
        deadline = time.time() + 300 * len(tasks)
        while time.time() < deadline:
            so_data = http_client.get(f"/api/wms/outbound/sales-orders/{so_id}").json()
            if so_data["status"] == "SHIPPED":
                break
            time.sleep(1.0)
        else:
            pytest.fail(
                f"Timed out ({300 * len(tasks)} s) waiting for order {so_ref} to reach SHIPPED "
                f"via manual picking"
            )
        print("[step] All picks confirmed — order shipped")

    else:
        # Auto mode: for each task, wait until it's at_dock then advance → complete.
        # Tasks at the same station are serialised naturally: only one can be at_dock
        # at a time; the next auto-promotes when the current one is advanced.
        pending = dict(tasks)
        total = len(pending)
        picks_done = 0
        deadline = time.time() + 60 * total

        while pending and time.time() < deadline:
            # Clear any at_dock tasks from OTHER orders that are blocking our
            # tasks from advancing (can happen when prior test runs left orders
            # in NEW state that got activated alongside ours by run_planning).
            our_stations = {d["station_id"] for d in pending.values()}
            for sid in our_stations:
                q = http_client.get(f"/api/wcs/stations/{sid}/queue").json()
                for t in q.get("tasks", []):
                    if t["status"] == "at_dock" and t["id"] not in pending:
                        http_client.post(f"/api/wcs/stations/{sid}/tasks/{t['id']}/advance")
                        http_client.post(f"/api/wcs/stations/{sid}/tasks/{t['id']}/complete")
                        print(f"[step] Cleared blocking task {t['id']} at {sid}")
                        break  # one at a time; re-check next iteration

            for task_id in list(pending.keys()):
                sid = pending[task_id]["station_id"]
                queue = http_client.get(f"/api/wcs/stations/{sid}/queue").json()
                task_now = next(
                    (t for t in queue.get("tasks", []) if t["id"] == task_id), None
                )

                if task_now is None or task_now["status"] == "completed":
                    del pending[task_id]
                    picks_done += 1
                    print(f"[step] Task {task_id} already completed ({picks_done}/{total})")
                    continue

                if task_now["status"] == "at_dock":
                    adv = http_client.post(f"/api/wcs/stations/{sid}/tasks/{task_id}/advance")
                    assert adv.status_code == 200, adv.text
                    comp = http_client.post(f"/api/wcs/stations/{sid}/tasks/{task_id}/complete")
                    assert comp.status_code == 200, comp.text
                    del pending[task_id]
                    picks_done += 1
                    print(f"[step] Task {task_id} at {sid} completed ({picks_done}/{total})")

            if pending:
                time.sleep(0.5)

        assert not pending, f"Tasks did not complete within timeout: {list(pending.keys())}"


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the order status is "{status}"'))
def check_order_status(http_client, ctx, status):
    so_data = http_client.get(f"/api/wms/outbound/sales-orders/{ctx['so_id']}").json()
    actual = so_data["status"]
    assert actual == status, f"Expected order status '{status}', got '{actual}'"
    print(f"[step] Order status: {actual}")


@then("a shipped shipment exists for the order")
def verify_shipment(http_client, ctx):
    resp = http_client.get("/api/wms/outbound/shipments", params={"so_id": ctx["so_id"]})
    assert resp.status_code == 200, resp.text
    shipments = resp.json()
    assert any(s["status"] == "SHIPPED" for s in shipments), (
        f"No SHIPPED shipment found for SO {ctx['so_id']}: {shipments}"
    )
    print(f"[step] Shipment verified — {len(shipments)} shipment(s) for order {ctx['so_ref']}")
    print(f"\n[PASS] {ctx['so_ref']} -> planned -> released -> AMR collected -> AMR delivered -> picked -> SHIPPED")

