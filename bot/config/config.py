from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    SECRET_KEY: str
    USE_PROXY_FROM_FILE: bool = False

    MIN_AVAILABLE_ENERGY: int = 10
    RANDOM_TAPS_COUNT: list[int] = [5, 9]
    SLEEP_BETWEEN_TAP: list[int] = [7, 15]
    AUTO_UPGRADE: bool = True


settings = Settings()
