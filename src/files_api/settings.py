from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    s3_bucket_name: str

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )
