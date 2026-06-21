"""Orders page object — read-only table of the user's order history."""

import logging
from typing import TypedDict

from .base_page import BasePage

logger = logging.getLogger("onsetto_scraper.pages.orders")


class OrderRow(TypedDict):
    order_id: str
    item: str
    total: str
    status: str
    date: str


class OrdersPage(BasePage):
    PATH = "/app/orders"

    async def navigate(self) -> None:
        await self._navigate(self.PATH)

    async def _column_indices(self) -> dict[str, int]:
        """Build a header-text → column-index map so row extraction is resilient to reordering."""
        headers = self._page.locator("table thead th")
        count = await headers.count()
        return {(await headers.nth(i).inner_text()).strip(): i for i in range(count)}

    async def get_orders(self) -> list[OrderRow]:
        """Return all rows from the orders table."""
        await self._wait_visible("table tbody")
        cols = await self._column_indices()
        rows = self._page.locator("table tbody tr")
        count = await rows.count()
        orders: list[OrderRow] = []
        for i in range(count):
            cells = rows.nth(i).locator("td")
            orders.append(
                OrderRow(
                    order_id=(await cells.nth(cols["Order ID"]).inner_text()).strip(),
                    item=(await cells.nth(cols["Item"]).inner_text()).strip(),
                    total=(await cells.nth(cols["Total"]).inner_text()).strip(),
                    status=(await cells.nth(cols["Status"]).inner_text()).strip(),
                    date=(await cells.nth(cols["Date"]).inner_text()).strip(),
                )
            )
        logger.info("Retrieved %d orders", len(orders))
        return orders
