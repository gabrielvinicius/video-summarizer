from pydantic_settings import BaseSettings
from pydantic import Field

class StorageSettings(BaseSettings):
    provider: str = Field("s3", alias="STORAGE_PROVIDER")
    bucket_name: str = Field(..., alias="BUCKET_NAME")
    endpoint_url: str = Field(..., alias="ENDPOINT_URL")
    access_key: str = Field(..., alias="ACCESS_KEY")
    secret_key: str = Field(..., alias="SECRET_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore"
