from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gtfs_static_url: str = "https://api.data.gov.my/gtfs-static/ktmb/"
    gtfs_realtime_url: str = "https://api.data.gov.my/gtfs-realtime/vehicle-position/ktmb/"
    user_agent: str = "ETS-Live-Malaysia/1.0 (MVP; contact: dev@example.com)"

    data_dir: Path = BASE_DIR / "data"
    gtfs_refresh_hours: int = 24
    realtime_poll_seconds: int = 30

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Optional secrets (set via env / platform secret store — never commit real values)
    api_key: str = ""  # If set, clients must send header X-API-Key
    admin_api_key: str = ""  # Required for POST /api/admin/* (header X-Admin-Key)
    data_gov_my_api_token: str = ""  # Optional Token from dataterbuka@jdn.gov.my

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
