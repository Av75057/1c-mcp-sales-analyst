from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt

from src.admin.database import get_db
from src.admin.multitenant.repository import TenantRepository
from src.admin.multitenant.encryption import encryptor

router = APIRouter(prefix="/api/v1/admin", tags=["multitenant"])


def _get_user_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(401, "Not authenticated")
    uid = getattr(user, "sub", None) or getattr(user, "id", None) or "admin"
    return uid


def _get_ip(request: Request) -> str:
    return request.client.host if request.client else ""


# === Tenants ===

@router.get("/tenants")
async def list_tenants(db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    return {"tenants": await repo.list_tenants()}


@router.post("/tenants")
async def create_tenant(body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    tenant = await repo.create_tenant(name=body["name"], slug=body.get("slug", body["name"].lower().replace(" ", "-")))
    await repo.log(actor_user_id=_get_user_id(request), action="tenant.create", resource_type="tenant", resource_id=tenant.id, tenant_id=tenant.id, ip=_get_ip(request))
    return {"tenant": {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}}


@router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    await repo.update_tenant(tenant_id, **{k: v for k, v in body.items() if k in ("name", "slug", "is_active", "settings")})
    await repo.log(actor_user_id=_get_user_id(request), action="tenant.update", resource_type="tenant", resource_id=tenant_id, tenant_id=tenant_id, ip=_get_ip(request))
    return {"status": "ok"}


# === Connections ===

@router.get("/connections")
async def list_connections(tenant_id: str = "", db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    if tenant_id and tenant_id != "all":
        return {"connections": await repo.list_connections(tenant_id)}
    # Return connections from all tenants
    tenants = await repo.list_tenants()
    all_conns = []
    for t in tenants:
        conns = await repo.list_connections(t["id"])
        all_conns.extend(conns)
    return {"connections": all_conns}


@router.post("/connections")
async def create_connection(body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    tenant_id = body.get("tenant_id", "")
    if not tenant_id:
        raise HTTPException(400, "tenant_id is required")
    conn = await repo.create_connection(
        tenant_id=tenant_id, name=body.get("name", "New Connection"),
        base_url=body.get("base_url", ""), username=body.get("username", ""),
        password=body.get("password", ""), is_default=body.get("is_default", False),
        timeout=body.get("timeout_seconds", 30),
    )
    await repo.log(actor_user_id=_get_user_id(request), action="connection.add", resource_type="connection", resource_id=conn.id, tenant_id=body["tenant_id"], ip=_get_ip(request))
    return {"connection": {"id": conn.id, "name": conn.name, "base_url": conn.base_url}}


@router.post("/connections/{conn_id}/test")
async def test_connection(conn_id: str, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    conn = await repo.get_connection(conn_id)
    if not conn:
        raise HTTPException(404, "Connection not found")
    password = encryptor.decrypt(conn["password_encrypted"]) if conn.get("password_encrypted") else ""
    import httpx
    try:
        raw = f"{conn['username']}:{password}"
        import base64
        auth = "Basic " + base64.b64encode(raw.encode("utf-8")).decode("ascii")
        start = __import__("time").time()
        async with httpx.AsyncClient(headers={"Authorization": auth}, timeout=10) as client:
            resp = await client.get(f"{conn['base_url'].rstrip('/')}/stock", params={"limit": "1"})
            latency = int((__import__("time").time() - start) * 1000)
            if resp.status_code < 500:
                await repo.set_health(conn_id, "ok")
                return {"status": "ok", "latency_ms": latency, "http_status": resp.status_code}
            else:
                await repo.set_health(conn_id, "error", resp.text[:200])
                return {"status": "error", "error": f"1C returned {resp.status_code}"}
    except Exception as e:
        await repo.set_health(conn_id, "error", str(e))
        return {"status": "error", "error": str(e)}


@router.patch("/connections/{conn_id}")
async def update_connection(conn_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    conn = await repo.get_connection(conn_id)
    if not conn:
        raise HTTPException(404, "Connection not found")
    updates = {k: v for k, v in body.items() if k in ("name", "base_url", "username", "password", "is_default", "timeout_seconds")}
    await repo.update_connection(conn_id, **updates)
    await repo.log(actor_user_id=_get_user_id(request), action="connection.update", resource_type="connection", resource_id=conn_id, ip=_get_ip(request))
    return {"status": "ok"}


@router.delete("/connections/{conn_id}")
async def delete_connection(conn_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    conn = await repo.get_connection(conn_id)
    if not conn:
        raise HTTPException(404, "Connection not found")
    await repo.delete_connection(conn_id)
    await repo.log(actor_user_id=_get_user_id(request), action="connection.delete", resource_type="connection", resource_id=conn_id, tenant_id=conn.get("tenant_id", ""), ip=_get_ip(request))
    return {"status": "deleted"}


# === Users ===

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    users = await repo.list_users()
    # Enrich with tenant info
    result = []
    for u in users:
        tenants_info = await repo.get_user_tenants(u["id"])
        u["tenants"] = tenants_info
        result.append(u)
    return {"users": result}


@router.post("/users")
async def create_user(body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    existing = await repo.get_user_by_email(body.get("email", ""))
    if existing:
        raise HTTPException(400, "User with this email already exists")
    password_hash = bcrypt.hash(body["password"])
    user = await repo.create_user(email=body.get("email", ""), password_hash=password_hash, full_name=body.get("full_name", ""), is_superadmin=body.get("is_superadmin", False))
    if body.get("tenant_id"):
        await repo.add_tenant_user(tenant_id=body["tenant_id"], user_id=user.id, role=body.get("role", "viewer"), allowed_connections=body.get("allowed_connection_ids"))
    await repo.log(actor_user_id=_get_user_id(request), action="user.create", resource_type="user", resource_id=user.id, ip=_get_ip(request))
    return {"user": {"id": user.id, "email": user.email, "full_name": user.full_name}}


@router.patch("/users/{user_id}")
async def update_user(user_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    updates = {k: v for k, v in body.items() if k in ("full_name", "is_active", "is_superadmin")}
    if "password" in body:
        updates["password_hash"] = bcrypt.hash(body["password"])
    if updates:
        await repo.update_user(user_id, **updates)
    await repo.log(actor_user_id=_get_user_id(request), action="user.update", resource_type="user", resource_id=user_id, ip=_get_ip(request))
    return {"status": "ok"}


# === Audit ===

@router.get("/audit")
async def list_audit(db: AsyncSession = Depends(get_db)):
    repo = TenantRepository(db)
    return {"entries": await repo.list_audit(limit=100)}
