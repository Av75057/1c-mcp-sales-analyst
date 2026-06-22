from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.logger import logger


class MockC1Client:
    def __init__(self) -> None:
        self._today = date.today()

    async def get_stock(
        self,
        warehouse: str | None = None,
        nomenclature: str | None = None,
        min_quantity: int | None = None,
    ) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = [
            {"nomenclature": "Гвоздь 100мм", "warehouse": "Москва", "quantity": 1500, "unit": "шт"},
            {"nomenclature": "Гвоздь 100мм", "warehouse": "СПб", "quantity": 800, "unit": "шт"},
            {"nomenclature": "Молоток", "warehouse": "Москва", "quantity": 45, "unit": "шт"},
            {"nomenclature": "Дрель ударная", "warehouse": "Москва", "quantity": 12, "unit": "шт"},
            {"nomenclature": "Шуруповёрт", "warehouse": "Москва", "quantity": 3, "unit": "шт"},
            {"nomenclature": "Перфоратор", "warehouse": "СПб", "quantity": 7, "unit": "шт"},
            {"nomenclature": "Лопата штыковая", "warehouse": "Москва", "quantity": 120, "unit": "шт"},
            {"nomenclature": "Ведро 10л", "warehouse": "Москва", "quantity": 200, "unit": "шт"},
            {"nomenclature": "Ведро 10л", "warehouse": "СПб", "quantity": 0, "unit": "шт"},
            {"nomenclature": "Саморез 50мм", "warehouse": "Москва", "quantity": 5000, "unit": "шт"},
            {"nomenclature": "Саморез 50мм", "warehouse": "СПб", "quantity": 0, "unit": "шт"},
            {"nomenclature": "Бетономешалка", "warehouse": "Москва", "quantity": 2, "unit": "шт"},
            {"nomenclature": "Уровень лазерный", "warehouse": "Москва", "quantity": 8, "unit": "шт"},
            {"nomenclature": "Рулетка 5м", "warehouse": "Москва", "quantity": 60, "unit": "шт"},
            {"nomenclature": "Рулетка 5м", "warehouse": "СПб", "quantity": 30, "unit": "шт"},
            {"nomenclature": "Краска акриловая 5кг", "warehouse": "Москва", "quantity": 25, "unit": "шт"},
            {"nomenclature": "Краска акриловая 5кг", "warehouse": "СПб", "quantity": 10, "unit": "шт"},
            {"nomenclature": "Кисть малярная 50мм", "warehouse": "Москва", "quantity": 100, "unit": "шт"},
            {"nomenclature": "Шпатель 100мм", "warehouse": "Москва", "quantity": 80, "unit": "шт"},
            {"nomenclature": "Шпатель 100мм", "warehouse": "СПб", "quantity": 40, "unit": "шт"},
            {"nomenclature": "Гайка М10", "warehouse": "Москва", "quantity": 2000, "unit": "шт"},
            {"nomenclature": "Болт М10х50", "warehouse": "Москва", "quantity": 1500, "unit": "шт"},
            {"nomenclature": "Болт М10х50", "warehouse": "СПб", "quantity": 600, "unit": "шт"},
            {"nomenclature": "Шайба М10", "warehouse": "Москва", "quantity": 3000, "unit": "шт"},
            {"nomenclature": "Набор ключей рожковых 6-24", "warehouse": "Москва", "quantity": 15, "unit": "шт"},
            {"nomenclature": "Горелка газовая", "warehouse": "Москва", "quantity": 5, "unit": "шт"},
            {"nomenclature": "Провод ПВС 3х1.5 50м", "warehouse": "Москва", "quantity": 18, "unit": "шт"},
            {"nomenclature": "Розетка наружная", "warehouse": "Москва", "quantity": 45, "unit": "шт"},
            {"nomenclature": "Выключатель одноклавишный", "warehouse": "Москва", "quantity": 60, "unit": "шт"},
            {"nomenclature": "Труба ПНД 25мм 10м", "warehouse": "Москва", "quantity": 22, "unit": "шт"},
        ]
        if warehouse:
            data = [d for d in data if d["warehouse"] == warehouse]
        if nomenclature:
            data = [d for d in data if nomenclature.lower() in d["nomenclature"].lower()]
        if min_quantity is not None:
            data = [d for d in data if d["quantity"] >= min_quantity]
        logger.debug("mock get_stock returned {} rows", len(data))
        return data

    async def get_sales(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        manager: str | None = None,
        warehouse: str | None = None,
    ) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = [
            {"date": (self._today - timedelta(days=1)).isoformat(), "nomenclature": "Гвоздь 100мм", "quantity": 200, "sum": 4000.0, "manager": "Иванов И.И.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=2)).isoformat(), "nomenclature": "Молоток", "quantity": 10, "sum": 3500.0, "manager": "Петров П.П.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=3)).isoformat(), "nomenclature": "Дрель ударная", "quantity": 3, "sum": 12000.0, "manager": "Иванов И.И.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=4)).isoformat(), "nomenclature": "Шуруповёрт", "quantity": 5, "sum": 25000.0, "manager": "Сидоров С.С.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=5)).isoformat(), "nomenclature": "Перфоратор", "quantity": 2, "sum": 14000.0, "manager": "Иванов И.И.", "warehouse": "СПб"},
            {"date": (self._today - timedelta(days=6)).isoformat(), "nomenclature": "Лопата штыковая", "quantity": 30, "sum": 4500.0, "manager": "Петров П.П.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=7)).isoformat(), "nomenclature": "Ведро 10л", "quantity": 50, "sum": 5000.0, "manager": "Сидоров С.С.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=8)).isoformat(), "nomenclature": "Бетономешалка", "quantity": 1, "sum": 35000.0, "manager": "Кузнецов К.К.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=9)).isoformat(), "nomenclature": "Саморез 50мм", "quantity": 1000, "sum": 8000.0, "manager": "Иванов И.И.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=10)).isoformat(), "nomenclature": "Краска акриловая 5кг", "quantity": 8, "sum": 9600.0, "manager": "Кузнецов К.К.", "warehouse": "СПб"},
            {"date": (self._today - timedelta(days=14)).isoformat(), "nomenclature": "Уровень лазерный", "quantity": 2, "sum": 16000.0, "manager": "Петров П.П.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=15)).isoformat(), "nomenclature": "Рулетка 5м", "quantity": 25, "sum": 3750.0, "manager": "Сидоров С.С.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=20)).isoformat(), "nomenclature": "Гайка М10", "quantity": 500, "sum": 2500.0, "manager": "Иванов И.И.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=21)).isoformat(), "nomenclature": "Болт М10х50", "quantity": 400, "sum": 3200.0, "manager": "Кузнецов К.К.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=25)).isoformat(), "nomenclature": "Гвоздь 100мм", "quantity": 100, "sum": 2000.0, "manager": "Петров П.П.", "warehouse": "СПб"},
            {"date": (self._today - timedelta(days=30)).isoformat(), "nomenclature": "Молоток", "quantity": 5, "sum": 1750.0, "manager": "Сидоров С.С.", "warehouse": "СПб"},
            {"date": (self._today - timedelta(days=35)).isoformat(), "nomenclature": "Розетка наружная", "quantity": 20, "sum": 4000.0, "manager": "Иванов И.И.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=40)).isoformat(), "nomenclature": "Выключатель одноклавишный", "quantity": 30, "sum": 4500.0, "manager": "Кузнецов К.К.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=45)).isoformat(), "nomenclature": "Труба ПНД 25мм 10м", "quantity": 5, "sum": 7500.0, "manager": "Петров П.П.", "warehouse": "Москва"},
            {"date": (self._today - timedelta(days=50)).isoformat(), "nomenclature": "Провод ПВС 3х1.5 50м", "quantity": 10, "sum": 9000.0, "manager": "Сидоров С.С.", "warehouse": "Москва"},
        ]
        if date_from:
            data = [d for d in data if d["date"] >= date_from]
        if date_to:
            data = [d for d in data if d["date"] <= date_to]
        if manager:
            data = [d for d in data if manager.lower() in d["manager"].lower()]
        if warehouse:
            data = [d for d in data if warehouse.lower() in d["warehouse"].lower()]
        logger.debug("mock get_sales returned {} rows", len(data))
        return data

    async def get_sales_by_manager(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        manager: str | None = None,
    ) -> list[dict[str, Any]]:
        sales = await self.get_sales(date_from=date_from, date_to=date_to, manager=manager)
        grouped: dict[str, dict[str, float | int]] = {}
        for s in sales:
            mgr = s["manager"]
            if mgr not in grouped:
                grouped[mgr] = {"manager": mgr, "total_sum": 0.0, "total_quantity": 0}
            grouped[mgr]["total_sum"] += s["sum"]
            grouped[mgr]["total_quantity"] += s["quantity"]
        result = list(grouped.values())
        logger.debug("mock get_sales_by_manager returned {} rows", len(result))
        return result

    async def get_purchases(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        item: str | None = None,
        supplier: str | None = None,
    ) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = [
            {"date": "2026-05-15", "item": "Гвоздь 100мм", "quantity": 500, "sum": 6250.0, "supplier": "ООО Метизы"},
            {"date": "2026-05-20", "item": "Саморез 50мм", "quantity": 1000, "sum": 3200.0, "supplier": "ООО Метизы"},
            {"date": "2026-06-01", "item": "Аренда виртуального сервера.", "quantity": 1, "sum": 3300.0, "supplier": "ООО Хостинг"},
            {"date": "2026-06-10", "item": "Краска акриловая 5кг", "quantity": 50, "sum": 22500.0, "supplier": "ИП Краски"},
        ]
        if item:
            data = [d for d in data if item.lower() in d["item"].lower()]
        if supplier:
            data = [d for d in data if supplier.lower() in d["supplier"].lower()]
        if date_from:
            data = [d for d in data if d["date"] >= date_from]
        if date_to:
            data = [d for d in data if d["date"] <= date_to]
        logger.debug("mock get_purchases returned {} rows", len(data))
        return data

    async def get_price_history(self, item: str, date_from: str | None = None, date_to: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return [{"date": "2026-01-01", "price": 100.0, "change_percent": 0}, {"date": "2026-03-01", "price": 110.0, "change_percent": 10.0}, {"date": "2026-05-01", "price": 120.0, "change_percent": 9.1}]

    async def get_purchase_orders(self, item: str | None = None, supplier: str | None = None, status: str = "open") -> list[dict[str, Any]]:
        return [{"date": "2026-06-15", "item": item or "Товар", "quantity": 500, "expected_date": "2026-06-25", "supplier": "ООО Метизы", "status": status, "days_overdue": 0}]

    async def get_item_movement(self, item: str, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, Any]]:
        return [{"date": "2026-06-15", "incoming": 500, "outgoing": 0}, {"date": "2026-06-16", "incoming": 0, "outgoing": 100}, {"date": "2026-06-17", "incoming": 0, "outgoing": 50}]

    async def get_receivables(
        self,
        min_amount: float | None = None,
        date_from: str | None = None,
    ) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = [
            {"client": "ООО СтройМастер", "amount": 250000.0, "overdue_days": 45},
            {"client": "АО РемонтСервис", "amount": 180000.0, "overdue_days": 30},
            {"client": "ИП Краснов", "amount": 75000.0, "overdue_days": 15},
            {"client": "ООО ДомСтрой", "amount": 320000.0, "overdue_days": 60},
            {"client": "ЗАО ТехноПром", "amount": 50000.0, "overdue_days": 10},
            {"client": "ООО СтройИнвест", "amount": 95000.0, "overdue_days": 20},
            {"client": "ИП Соколова", "amount": 12000.0, "overdue_days": 5},
            {"client": "ООО РемонтСтрой", "amount": 400000.0, "overdue_days": 90},
            {"client": "АО МонтажСервис", "amount": 150000.0, "overdue_days": 35},
            {"client": "ООО ЭнергоСтрой", "amount": 60000.0, "overdue_days": 12},
        ]
        if min_amount is not None:
            data = [d for d in data if d["amount"] >= min_amount]
        if date_from:
            data = [d for d in data if d["overdue_days"] >= 0]
        logger.debug("mock get_receivables returned {} rows", len(data))
        return data

    async def list_nomenclature(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        data = [
            {"ref": "00000001", "name": "Гвоздь 100мм", "unit": "шт"},
            {"ref": "00000002", "name": "Гвоздь 80мм", "unit": "шт"},
            {"ref": "00000003", "name": "Молоток", "unit": "шт"},
            {"ref": "00000004", "name": "Дрель ударная", "unit": "шт"},
            {"ref": "00000005", "name": "Шуруповёрт", "unit": "шт"},
            {"ref": "00000006", "name": "Перфоратор", "unit": "шт"},
            {"ref": "00000007", "name": "Лопата штыковая", "unit": "шт"},
            {"ref": "00000008", "name": "Ведро 10л", "unit": "шт"},
            {"ref": "00000009", "name": "Саморез 50мм", "unit": "шт"},
            {"ref": "00000010", "name": "Бетономешалка", "unit": "шт"},
            {"ref": "00000011", "name": "Уровень лазерный", "unit": "шт"},
            {"ref": "00000012", "name": "Рулетка 5м", "unit": "шт"},
            {"ref": "00000013", "name": "Краска акриловая 5кг", "unit": "шт"},
            {"ref": "00000014", "name": "Кисть малярная 50мм", "unit": "шт"},
            {"ref": "00000015", "name": "Шпатель 100мм", "unit": "шт"},
            {"ref": "00000016", "name": "Гайка М10", "unit": "шт"},
            {"ref": "00000017", "name": "Болт М10х50", "unit": "шт"},
            {"ref": "00000018", "name": "Шайба М10", "unit": "шт"},
            {"ref": "00000019", "name": "Набор ключей рожковых 6-24", "unit": "шт"},
            {"ref": "00000020", "name": "Горелка газовая", "unit": "шт"},
            {"ref": "00000021", "name": "Провод ПВС 3х1.5 50м", "unit": "шт"},
            {"ref": "00000022", "name": "Розетка наружная", "unit": "шт"},
            {"ref": "00000023", "name": "Выключатель одноклавишный", "unit": "шт"},
            {"ref": "00000024", "name": "Труба ПНД 25мм 10м", "unit": "шт"},
            {"ref": "00000025", "name": "Шлифмашина угловая", "unit": "шт"},
            {"ref": "00000026", "name": "Лобзик", "unit": "шт"},
            {"ref": "00000027", "name": "Ножовка", "unit": "шт"},
            {"ref": "00000028", "name": "Стамеска", "unit": "шт"},
            {"ref": "00000029", "name": "Плоскогубцы", "unit": "шт"},
            {"ref": "00000030", "name": "Отвёртка крестовая", "unit": "шт"},
        ]
        filtered = [d for d in data if query.lower() in d["name"].lower()]
        result = filtered[:limit]
        logger.debug("mock list_nomenclature returned {} rows", len(result))
        return result

    async def close(self) -> None:
        pass
