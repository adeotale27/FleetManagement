from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "OI Pulse Fleet"
    app_version: str = "0.1.0"
    secret_key: str = "dev-secret-change-me"
    jwt_secret: str = "dev-jwt-secret-change-me-32chars!!"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "fleet_logistics"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    storage_dir: str = "./data/storage"
    run_seed: bool = False
    rate_limit_per_minute: int = 120
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
