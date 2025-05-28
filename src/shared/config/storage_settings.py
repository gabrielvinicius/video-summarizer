from pydantic_settings import BaseSettings

class StorageSettings(BaseSettings):
    storage_provider: str = "local"  # s3 | local | ftp
    bucket_name: str
    endpoint_url: str
    access_key: str
    secret_key: str

    class Config:
        env_file = ".env"
        extra = "ignore"
