from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Any

from src.logger import logger


async def export_pdf(data: list[dict[str, Any]], meta: dict[str, Any] | None = None, chart_image_b64: str | None = None, options: dict | None = None) -> io.BytesIO:
    """Экспорт дашборда в PDF через WeasyPrint."""
    opts = options or {}

    try:
        from weasyprint import HTML
    except ImportError:
        logger.error("WeasyPrint not installed. Install with: pip install weasyprint")
        raise RuntimeError("WeasyPrint is required for PDF export")

    title = (meta or {}).get("title", "Дашборд")
    description = (meta or {}).get("description", "")
    query = (meta or {}).get("original_query", "")

    include_data_table = opts.get("include_data_table", True)
    include_metadata = opts.get("include_metadata", True)

    columns = list(data[0].keys()) if data else []

    # Строим HTML для PDF
    rows_html = ""
    if data and include_data_table:
        for row in data[:100]:
            rows_html += "<tr>" + "".join(f"<td>{row.get(c, '')}</td>" for c in columns) + "</tr>"

    chart_html = ""
    if chart_image_b64:
        chart_html = f'<img class="chart" src="data:image/png;base64,{chart_image_b64}" />'

    meta_html = ""
    if include_metadata:
        meta_html = f"""
        <div class="meta">
            <p><strong>Сформировано:</strong> {datetime.utcnow().strftime("%d.%m.%Y %H:%M")} UTC</p>
            <p><strong>Источник:</strong> 1С:УНФ</p>
            <p><strong>Запрос:</strong> {query}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
    @page {{ size: {opts.get("paper_size", "A4")} {opts.get("orientation", "landscape")}; margin: 2cm; }}
    body {{ font-family: 'DejaVu Sans', sans-serif; font-size: 11px; color: #333; }}
    .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #2563eb; padding-bottom: 15px; }}
    .title {{ font-size: 22px; font-weight: bold; color: #1e3a5f; }}
    .desc {{ font-size: 13px; color: #666; margin-top: 5px; }}
    .chart {{ width: 100%; max-height: 450px; margin: 20px 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px; }}
    th {{ background: #2563eb; color: white; padding: 8px; text-align: left; }}
    td {{ border: 1px solid #ddd; padding: 6px; }}
    tr:nth-child(even) {{ background: #f8f9fa; }}
    .meta {{ margin-top: 40px; font-size: 9px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }}
    .footer {{ text-align: center; font-size: 9px; color: #999; margin-top: 20px; }}
</style></head><body>
    <div class="header">
        <div class="title">{title}</div>
        {f'<div class="desc">{description}</div>' if description else ''}
    </div>
    {chart_html}
    {f'<table><thead><tr>{"".join(f"<th>{c}</th>" for c in columns)}</tr></thead><tbody>{rows_html}</tbody></table>' if data and include_data_table else ''}
    {f'<p style="color:#999;text-align:center">Показано {min(len(data), 100)} из {len(data)} записей</p>' if data and len(data) > 100 else ''}
    {meta_html}
    <div class="footer">Страница 1 из 1</div>
</body></html>"""

    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf)
    buf.seek(0)
    return buf
