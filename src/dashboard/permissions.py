from __future__ import annotations

from typing import Any

# Лимиты и квоты
LIBRARY_LIMITS = {
    "max_dashboards_per_user": 500,
    "max_tags_per_dashboard": 20,
    "max_title_length": 200,
    "max_description_length": 2000,
    "max_tag_length": 50,
    "max_shares_per_dashboard": 50,
    "max_share_ttl_days": 90,
    "exports_per_hour": 100,
    "query_cache_ttl_seconds": 900,
    "metadata_cache_ttl_hours": 1,
    "max_query_cache_entries": 10000,
}


class DashboardPermissions:
    """Матрица прав доступа к дашбордам."""

    PERMISSIONS = {
        "owner": ["view", "edit", "delete", "share", "export"],
        "viewer": ["view", "export"],
        "editor": ["view", "edit", "export"],
        "public": ["view"],
    }

    @staticmethod
    def check(dashboard: dict, user_id: str, permission: str) -> bool:
        role = DashboardPermissions._get_role(dashboard, user_id)
        return permission in DashboardPermissions.PERMISSIONS.get(role, [])

    @staticmethod
    def _get_role(dashboard: dict, user_id: str) -> str:
        if dashboard.get("owner_id") == user_id:
            return "owner"
        if dashboard.get("is_public"):
            return "public"
        return "viewer"

    @staticmethod
    def can_view(dashboard: dict, user_id: str) -> bool:
        return DashboardPermissions.check(dashboard, user_id, "view")

    @staticmethod
    def can_edit(dashboard: dict, user_id: str) -> bool:
        return DashboardPermissions.check(dashboard, user_id, "edit")

    @staticmethod
    def can_delete(dashboard: dict, user_id: str) -> bool:
        return DashboardPermissions.check(dashboard, user_id, "delete")

    @staticmethod
    def can_share(dashboard: dict, user_id: str) -> bool:
        return DashboardPermissions.check(dashboard, user_id, "share")

    @staticmethod
    def get_permissions(dashboard: dict, user_id: str) -> dict[str, bool]:
        return {
            "can_view": DashboardPermissions.can_view(dashboard, user_id),
            "can_edit": DashboardPermissions.can_edit(dashboard, user_id),
            "can_delete": DashboardPermissions.can_delete(dashboard, user_id),
            "can_share": DashboardPermissions.can_share(dashboard, user_id),
        }
