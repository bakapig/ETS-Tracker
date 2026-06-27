from app.config import settings


def outbound_headers() -> dict[str, str]:
    """Headers for Malaysia Open API (data.gov.my) requests."""
    headers = {"User-Agent": settings.user_agent}
    if settings.data_gov_my_api_token:
        headers["Authorization"] = f"Token {settings.data_gov_my_api_token}"
    return headers
