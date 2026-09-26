"""Verified user-supplied market comparables; never inferred from imagery."""
from __future__ import annotations

import statistics
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException

from .schemas import PriceComparable, PriceComparableCreate, PriceSummary
from .storage import Store


def add_comparable(store: Store, location_id: str, request: PriceComparableCreate) -> PriceComparable:
    if not store.get("location", location_id):
        raise HTTPException(status_code=404, detail="monitored location not found")
    comparable = PriceComparable(
        **request.model_dump(), id=uuid.uuid4().hex, location_id=location_id,
        price_per_ha=round(request.total_price / request.area_ha, 2), created_at=datetime.now(UTC),
    )
    store.put("price_comparable", comparable.id, comparable.model_dump(mode="json"))
    return comparable


def price_summary(store: Store, location_id: str) -> PriceSummary:
    if not store.get("location", location_id):
        raise HTTPException(status_code=404, detail="monitored location not found")
    values = [PriceComparable.model_validate(item) for item in store.list("price_comparable") if item.get("location_id") == location_id]
    values.sort(key=lambda item: item.transaction_date)
    currencies = {item.currency.upper() for item in values}
    if len(currencies) > 1:
        raise HTTPException(status_code=422, detail="price comparables must use one currency; currency conversion is not inferred")
    prices = [item.price_per_ha for item in values]
    change = None
    direction = "insufficient_data"
    if len(prices) >= 2 and prices[0]:
        change = round((prices[-1] - prices[0]) / prices[0] * 100, 2)
        direction = "up" if change > 1 else "down" if change < -1 else "flat"
    return PriceSummary(
        location_id=location_id, comparable_count=len(values), currency=next(iter(currencies), None),
        median_price_per_ha=round(statistics.median(prices), 2) if prices else None,
        min_price_per_ha=min(prices) if prices else None, max_price_per_ha=max(prices) if prices else None,
        first_to_latest_change_pct=change, trend_direction=direction, comparables=values,
        caveat="This summary uses only entered transaction/asking-price evidence. It is not a valuation, market index, or satellite-derived price.",
    )
