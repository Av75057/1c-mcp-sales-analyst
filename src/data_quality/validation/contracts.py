from __future__ import annotations

from typing import Any

from src.data_quality.models.sales import SalesRecord
from src.data_quality.models.stock import StockRecord

TOOL_CONTRACTS: dict[str, dict[str, Any]] = {
    "get_sales": {
        "output_model": SalesRecord,
        "quality_rules": ["positive_amount", "valid_date"],
    },
    "get_stock": {
        "output_model": StockRecord,
        "quality_rules": ["non_negative"],
    },
    "get_sales_by_manager": {
        "output_model": SalesRecord,
        "quality_rules": [],
    },
}
