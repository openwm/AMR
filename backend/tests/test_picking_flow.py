"""
Integration test for the end-to-end outbound picking flow.

Requires the stack to be running: docker compose up
Run: pytest backend/tests/test_picking_flow.py -v -s
"""
import time

import httpx
import pytest

BASE = "http://localhost:8000"


def _clear_wcs_tasks(client: httpx.Client) -> None:
    """Exception all non-terminal WCS tasks to free station capacity before the test."""
    stations = client.get("/api/wcs/stations").json()
    for s in stations:
        sid = s["station_id"]
        if s.get("queue_depth", 0) == 0 and s.get("amr_count", 0) == 0:
            continue
        queue = client.get(f"/api/wcs/stations/{sid}/queue").json()
        for t in queue.get("tasks", []):
            if t["status"] not in ("completed", "exception"):
                try:
                    client.post(f"/api/wcs/stations/{sid}/tasks/{t['id']}/exception")
                except Exception:
                    pass


def test_picking_flow_end_to_end(manual: bool) -> None:
    client = httpx.Client(base_url=BASE, timeout=15.0)

    # Pre-clean: exception any queued/active WCS tasks so stations have free capacity
    _clear_wcs_tasks(client)

    # Step 1: find a product with available stock
    stock_resp = client.get("/api/wms/inventory/stock")
    assert stock_resp.status_code == 200, stock_resp.text
    available = [s for s in stock_resp.json() if s["status"] == "AVAILABLE" and s["quantity"] > 0]
    if not available:
        pytest.skip("No available stock — seed data required")

    product_id = available[0]["product_id"]
    print(f"\n[test] Using product_id={product_id}")

    # Step 2: create a new SO with 1 line, qty 1
    ref = f"TEST-PICK-{int(time.time())}"
    so_resp = client.post(
        "/api/wms/outbound/sales-orders",
        json={
            "reference": ref,
            "customer": "Integration Test",
            "lines": [{"product_id": product_id, "qty_ordered": 1}],
        },
    )
    assert so_resp.status_code == 201, so_resp.text
    so = so_resp.json()
    so_id = so["id"]
    line_id = so["lines"][0]["id"]
    print(f"[test] Created SO id={so_id} ref={ref} line_id={line_id}")

    # Step 3: run planning to activate the SO
    plan_resp = client.post("/api/wms/planning/run")
    assert plan_resp.status_code == 200, plan_resp.text
    print(f"[test] Planning result: {plan_resp.json()}")

    # Step 4: verify SO is now ACTIVE
    so_data = client.get(f"/api/wms/outbound/sales-orders/{so_id}").json()
    assert so_data["status"] == "ACTIVE", f"Expected ACTIVE, got {so_data['status']}"
    print(f"[test] SO status: {so_data['status']}")

    # Step 5: release to WCS
    rel_resp = client.post("/api/wms/planning/release")
    assert rel_resp.status_code == 200, rel_resp.text
    rel_result = rel_resp.json()
    print(f"[test] Release result: {rel_result}")

    # Step 6: verify our SO is now PICKING
    so_data = client.get(f"/api/wms/outbound/sales-orders/{so_id}").json()
    assert so_data["status"] == "PICKING", f"Expected PICKING, got {so_data['status']}"
    print(f"[test] SO status: {so_data['status']}")

    # Step 7: find the task for our SO in WCS station queues
    stations_resp = client.get("/api/wcs/stations")
    assert stations_resp.status_code == 200
    stations = stations_resp.json()

    station_id = None
    task_id = None
    for s in stations:
        sid = s["station_id"]
        queue = client.get(f"/api/wcs/stations/{sid}/queue").json()
        for t in queue.get("tasks", []):
            if t["order_id"] == so_id and t["order_line_id"] == line_id:
                station_id = sid
                task_id = t["id"]
                break
        if task_id:
            break

    assert task_id is not None, f"Task for SO {so_id} / line {line_id} not found in any station queue"
    print(f"[test] Found task_id={task_id} at station={station_id}")

    # Step 8: wait for task to reach at_dock (it auto-promotes when dock is empty)
    task_status = None
    for _ in range(10):
        queue = client.get(f"/api/wcs/stations/{station_id}/queue").json()
        task = next((t for t in queue.get("tasks", []) if t["id"] == task_id), None)
        if task:
            task_status = task["status"]
            if task_status == "at_dock":
                break
        time.sleep(0.5)
    else:
        pytest.fail(f"Task never reached at_dock; last status: {task_status}")
    print("[test] Task is at_dock — AMR arrived at station")

    if manual:
        # Manual mode: let the operator click "Confirm Pick" in the GUI
        print(f"\n[MANUAL] Open the picking station GUI and confirm the pick:")
        print(f"[MANUAL]   http://localhost:5173/devices/picking/{station_id}")
        print(f"[MANUAL] Task {task_id} is waiting at the dock — click 'Confirm Pick'.\n")
        # Poll until the task disappears or reaches completed/exception (5-min timeout)
        for _ in range(600):
            queue = client.get(f"/api/wcs/stations/{station_id}/queue").json()
            task = next((t for t in queue.get("tasks", []) if t["id"] == task_id), None)
            if task is None or task["status"] in ("completed", "exception"):
                break
            time.sleep(0.5)
        else:
            pytest.fail("Timed out (5 min) waiting for manual pick confirmation")
        print("[test] Manual pick confirmed — task completed")
    else:
        # Step 9: advance at_dock → picking (operator begins pick)
        adv_resp = client.post(f"/api/wcs/stations/{station_id}/tasks/{task_id}/advance")
        assert adv_resp.status_code == 200, adv_resp.text
        assert adv_resp.json()["status"] == "picking"
        print("[test] Task advanced to picking")

        # Step 10: complete picking → completed (triggers WCS→WMS PATCH callback)
        comp_resp = client.post(f"/api/wcs/stations/{station_id}/tasks/{task_id}/complete")
        assert comp_resp.status_code == 200, comp_resp.text
        assert comp_resp.json()["status"] == "completed"
        print("[test] Task completed — WCS callback sent to WMS")

    # Step 11: wait for SO to become SHIPPED (auto-ship triggered by WMS callback)
    so_status = None
    for _ in range(10):
        so_data = client.get(f"/api/wms/outbound/sales-orders/{so_id}").json()
        so_status = so_data["status"]
        if so_status == "SHIPPED":
            break
        time.sleep(0.5)
    else:
        pytest.fail(f"SO never reached SHIPPED; last status: {so_status}")
    print(f"[test] SO status: {so_status}")

    # Step 12: verify an auto-created shipment exists and is SHIPPED
    shipments_resp = client.get("/api/wms/outbound/shipments", params={"so_id": so_id})
    assert shipments_resp.status_code == 200
    shipments = shipments_resp.json()
    assert any(s["status"] == "SHIPPED" for s in shipments), f"No SHIPPED shipment found: {shipments}"
    print(f"[test] Shipment verified — {len(shipments)} shipment(s)")

    print(f"\n[test] PASS: {ref} → planned → released → AMR delivered → picked → SHIPPED")
