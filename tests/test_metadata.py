from __future__ import annotations

from src.metadata.service import metadata_service


class TestMetadataService:
    async def test_get_config(self):
        cfg = await metadata_service.get_config()
        assert "name" in cfg
        assert "version" in cfg

    async def test_config_is_cached(self):
        cfg1 = await metadata_service.get_config()
        cfg2 = await metadata_service.get_config()
        assert cfg1 == cfg2

    async def test_describe_all(self):
        objects = await metadata_service.describe()
        assert len(objects) >= 4

    async def test_describe_by_type(self):
        objects = await metadata_service.describe(object_type="Catalog")
        assert all(o["type"] == "Catalog" for o in objects)

    async def test_describe_by_search(self):
        objects = await metadata_service.describe(search="Номенклатура")
        assert len(objects) >= 1
        assert objects[0]["name"] == "Номенклатура"

    async def test_describe_no_results(self):
        objects = await metadata_service.describe(search="xxxxnonexistent12345")
        assert len(objects) == 0

    async def test_get_structure(self):
        struct = await metadata_service.get_structure("Номенклатура")
        assert struct["name"] == "Номенклатура"
        assert "fields" in struct

    async def test_get_structure_cached(self):
        s1 = await metadata_service.get_structure("Товары")
        s2 = await metadata_service.get_structure("Товары")
        assert s1 == s2

    async def test_invalidate_cache(self):
        count = await metadata_service.invalidate_cache()
        assert count >= 0
