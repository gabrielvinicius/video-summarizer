from pydantic_settings import BaseSettings

class StorageSettings(BaseSettings):
    provider: str = "s3"  # s3 | local | ftp
    bucket_name: str
    endpoint_url: str
    access_key: str
    secret_key: str

    class Config:
        env_file = ".env"
        extra = "ignore"
