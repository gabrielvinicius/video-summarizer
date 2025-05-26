from pydantic_settings import BaseSettings

class LLMSettings(BaseSettings):
    provider: str = "openai"  # openai | transformers
    openai_api_key: str = ""
    transformers_model: str = "facebook/bart-large-cnn"

    class Config:
        env_file = ".env"
        extra = "ignore"
