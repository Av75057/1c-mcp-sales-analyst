from __future__ import annotations

import time
from typing import Any

from src.logger import logger

METADATA_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 3600


class MetadataService:
    def __init__(self) -> None:
        self._cache = METADATA_CACHE

    async def get_config(self) -> dict[str, Any]:
        if cached := self._cache.get("config"):
            if time.time() - cached[0] < CACHE_TTL:
                return cached[1]
        config = {"name": "1С:УНФ", "configuration": "УНФ", "version": "1.0", "mode": "production", "server": "1c.company.ru"}
        self._cache["config"] = (time.time(), config)
        return config

    async def describe(self, object_type: str | None = None, search: str | None = None) -> list[dict[str, Any]]:
        objects = [
            {"name": "Номенклатура", "type": "Catalog", "fields_count": 25, "description": "Товары и услуги"},
            {"name": "Контрагенты", "type": "Catalog", "fields_count": 30, "description": "Контрагенты"},
            {"name": "Организации", "type": "Catalog", "fields_count": 15, "description": "Собственные организации"},
            {"name": "Склады", "type": "Catalog", "fields_count": 10, "description": "Места хранения"},
            {"name": "Кассы", "type": "Catalog", "fields_count": 8, "description": "Кассы"},
            {"name": "БанковскиеСчета", "type": "Catalog", "fields_count": 12, "description": "Банковские счета"},
            {"name": "Валюты", "type": "Catalog", "fields_count": 5, "description": "Валюты"},
            {"name": "ЕдиницыИзмерения", "type": "Catalog", "fields_count": 5, "description": "Единицы измерения"},
            {"name": "Пользователи", "type": "Catalog", "fields_count": 10, "description": "Пользователи"},
            {"name": "РеализацияТоваровУслуг", "type": "Document", "fields_count": 20, "description": "Продажи товаров и услуг"},
            {"name": "ПоступлениеТоваровУслуг", "type": "Document", "fields_count": 20, "description": "Закупки товаров и услуг"},
            {"name": "СчетФактураВыданный", "type": "Document", "fields_count": 15, "description": "Счета-фактуры выданные"},
            {"name": "ЗаказПокупателя", "type": "Document", "fields_count": 18, "description": "Заказы покупателей"},
            {"name": "ЗаказПоставщику", "type": "Document", "fields_count": 18, "description": "Заказы поставщикам"},
            {"name": "ВозвратТоваровПокупателю", "type": "Document", "fields_count": 15, "description": "Возвраты"},
            {"name": "Продажи", "type": "AccumulationRegister", "fields_count": 8, "description": "Обороты продаж"},
            {"name": "Закупки", "type": "AccumulationRegister", "fields_count": 8, "description": "Обороты закупок"},
            {"name": "ЗапасыНаСкладах", "type": "AccumulationRegister", "fields_count": 6, "description": "Остатки товаров"},
            {"name": "Взаиморасчеты", "type": "AccumulationRegister", "fields_count": 6, "description": "Взаиморасчеты с контрагентами"},
            {"name": "ЦеныНоменклатуры", "type": "InformationRegister", "fields_count": 5, "description": "Цены номенклатуры"},
        ]
        if object_type:
            objects = [o for o in objects if o["type"].lower() == object_type.lower()]
        if search:
            try:
                from rapidfuzz import fuzz
                objects = [o for o in objects if fuzz.partial_ratio(search.lower(), o["name"].lower()) > 60]
            except ImportError:
                objects = [o for o in objects if search.lower() in o["name"].lower()]
        return objects

    async def get_structure(self, object_name: str) -> dict[str, Any]:
        cache_key = f"structure_{object_name}"
        if cached := self._cache.get(cache_key):
            if time.time() - cached[0] < CACHE_TTL:
                return cached[1]

        structures: dict[str, dict[str, Any]] = {
            "Номенклатура": {"name": "Номенклатура", "type": "Catalog", "fields": [
                {"name": "Наименование", "type": "String", "length": 100}, {"name": "Код", "type": "String", "length": 25},
                {"name": "Артикул", "type": "String", "length": 25}, {"name": "ЕдиницаИзмерения", "type": "CatalogRef.ЕдиницыИзмерения"},
                {"name": "ТипНоменклатуры", "type": "Enum"}, {"name": "ВидНоменклатуры", "type": "CatalogRef.ВидыНоменклатуры"},
                {"name": "СтавкаНДС", "type": "Enum"}, {"name": "Цена", "type": "Number", "precision": 10, "scale": 2},
                {"name": "Комментарий", "type": "String", "length": 200}, {"name": "ПометкаУдаления", "type": "Boolean"},
            ]},
            "Контрагенты": {"name": "Контрагенты", "type": "Catalog", "fields": [
                {"name": "Наименование", "type": "String", "length": 100}, {"name": "Код", "type": "String", "length": 25},
                {"name": "ИНН", "type": "String", "length": 12}, {"name": "КПП", "type": "String", "length": 9},
                {"name": "ОГРН", "type": "String", "length": 15}, {"name": "ЮрФизЛицо", "type": "Enum"},
                {"name": "Телефон", "type": "String", "length": 20}, {"name": "Email", "type": "String", "length": 50},
                {"name": "Адрес", "type": "String", "length": 200}, {"name": "Контрагент", "type": "Boolean"},
            ]},
            "Продажи": {"name": "Продажи", "type": "AccumulationRegister", "fields": [
                {"name": "Период", "type": "DateTime"}, {"name": "Номенклатура", "type": "CatalogRef.Номенклатура"},
                {"name": "Контрагент", "type": "CatalogRef.Контрагенты"}, {"name": "Менеджер", "type": "CatalogRef.Пользователи"},
                {"name": "Количество", "type": "Number", "precision": 15, "scale": 3},
                {"name": "Сумма", "type": "Number", "precision": 15, "scale": 2},
                {"name": "Себестоимость", "type": "Number", "precision": 15, "scale": 2},
            ]},
            "ЗапасыНаСкладах": {"name": "ЗапасыНаСкладах", "type": "AccumulationRegister", "fields": [
                {"name": "Номенклатура", "type": "CatalogRef.Номенклатура"}, {"name": "Склад", "type": "CatalogRef.Склады"},
                {"name": "КоличествоОстаток", "type": "Number", "precision": 15, "scale": 3},
                {"name": "СуммаОстаток", "type": "Number", "precision": 15, "scale": 2},
            ]},
            "Закупки": {"name": "Закупки", "type": "AccumulationRegister", "fields": [
                {"name": "Период", "type": "DateTime"}, {"name": "Номенклатура", "type": "CatalogRef.Номенклатура"},
                {"name": "Контрагент", "type": "CatalogRef.Контрагенты"}, {"name": "Количество", "type": "Number"},
                {"name": "Сумма", "type": "Number"},
            ]},
        }

        stock = structures.get(object_name)
        if stock:
            self._cache[cache_key] = (time.time(), stock)
            return stock

        structure = {"name": object_name, "type": "Catalog", "fields": [{"name": "Наименование", "type": "String"}, {"name": "Код", "type": "String"}]}
        self._cache[cache_key] = (time.time(), structure)
        return structure

    async def invalidate_cache(self) -> int:
        count = len(self._cache)
        self._cache.clear()
        return count


metadata_service = MetadataService()
