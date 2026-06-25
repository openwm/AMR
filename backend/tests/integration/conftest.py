import httpx
import pytest

BASE = "http://localhost:8000"
AMR_SIM_BASE = "http://localhost:8001"


@pytest.fixture
def http_client():
    with httpx.Client(base_url=BASE, timeout=15.0) as client:
        yield client


@pytest.fixture
def amr_sim_client():
    with httpx.Client(base_url=AMR_SIM_BASE, timeout=10.0) as client:
        yield client


@pytest.fixture
def ctx():
    """Mutable dict shared between all Gherkin steps within a single scenario."""
    return {}


def clear_wcs_tasks(client: httpx.Client) -> None:
    """Exception all non-terminal WCS tasks across every station."""
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


def ensure_amr_fleet(amr_client: httpx.Client, min_count: int = 2) -> None:
    """Register AMRs until the fleet has at least min_count members."""
    amrs = amr_client.get("/amrs").json()
    for i in range(max(0, min_count - len(amrs))):
        n = len(amrs) + i + 1
        amr_client.post("/amrs", json={"name": f"AMR-{n:02d}", "x": 0.0, "y": 0.0})


_TEST_PREFIXES = ("BDD-PICK-", "TEST-PICK-", "INTEG-PICK-")


def force_close_test_orders(client: httpx.Client) -> int:
    """
    Force-ship any test orders stuck in ACTIVE or PICKING state by patching
    every unfulfilled line to its full qty_ordered. This triggers the existing
    auto-ship path (record_line_picked → _auto_ship) without requiring a
    dedicated cancel endpoint.  Returns the number of orders closed.
    """
    closed = 0
    for status in ("ACTIVE", "PICKING"):
        resp = client.get("/api/wms/outbound/sales-orders", params={"status_filter": status})
        if resp.status_code != 200:
            continue
        for so in resp.json():
            if not any(so.get("reference", "").startswith(p) for p in _TEST_PREFIXES):
                continue
            so_id = so["id"]
            detail = client.get(f"/api/wms/outbound/sales-orders/{so_id}")
            if detail.status_code != 200:
                continue
            for line in detail.json().get("lines", []):
                remaining = line.get("qty_ordered", 0) - line.get("qty_picked", 0)
                if remaining > 0:
                    client.patch(
                        f"/api/wms/outbound/sales-orders/{so_id}/lines/{line['id']}",
                        json={"picked_qty": remaining},
                    )
            closed += 1
    return closed
