from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

_client_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_client_api_key(
    api_key: str | None = Security(_client_key_header),
) -> None:
    """Optional gate for mobile/web clients. Skipped when API_KEY is unset."""
    if not settings.api_key:
        return
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


async def require_admin_key(
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
) -> None:
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin endpoint not configured")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Forbidden")
