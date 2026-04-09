from __future__ import annotations

import asyncio
import importlib
import os
import sys
import unittest
from pathlib import Path

import httpx

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


class OpenMetricsApiTest(unittest.TestCase):
    def _load_app(self, base_path: str):
        module_name = "openMetricsMicroservice.app"
        previous = os.environ.get("API_BASE_PATH")
        os.environ["API_BASE_PATH"] = base_path
        try:
            sys.modules.pop(module_name, None)
            module = importlib.import_module(module_name)
            return module.app, module.EVENT_COUNTER, module.STATUS_COUNTER
        finally:
            if previous is None:
                os.environ.pop("API_BASE_PATH", None)
            else:
                os.environ["API_BASE_PATH"] = previous

    async def _request(self, app, method: str, path: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    def test_metrics_available_with_and_without_base_path(self) -> None:
        app, event_counter, status_counter = self._load_app("/pi1-productinventorymanagement")
        event_counter.clear()
        status_counter.clear()

        direct_response = asyncio.run(self._request(app, "GET", "/metrics"))
        self.assertEqual(direct_response.status_code, 200)
        self.assertIn("tmfc005_product_inventory_events_total", direct_response.text)

        base_response = asyncio.run(self._request(app, "GET", "/pi1-productinventorymanagement/metrics"))
        self.assertEqual(base_response.status_code, 200)
        self.assertIn("tmfc005_product_inventory_events_total", base_response.text)
