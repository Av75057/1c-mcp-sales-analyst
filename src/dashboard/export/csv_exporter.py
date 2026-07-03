from __future__ import annotations

import csv
import io
from typing import Any


def export_csv(data: list[dict[str, Any]]) -> str:
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()
