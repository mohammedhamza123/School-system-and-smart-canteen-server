import os
from pathlib import Path

from pydantic import BaseModel

_backend_root = Path(__file__).resolve().parents[2]
_default_firebase_credentials = _backend_root / "firebase-service-account.json"


class Settings(BaseModel):
    app_name: str = "Smart School Canteen API"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./canteen.db"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    firebase_credentials_path: str | None = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        str(_default_firebase_credentials) if _default_firebase_credentials.exists() else None,
    )
    firebase_notifications_enabled: bool = (
        os.getenv("FIREBASE_NOTIFICATIONS_ENABLED", "true").strip().lower()
        not in {"0", "false", "no"}
    )


settings = Settings()
