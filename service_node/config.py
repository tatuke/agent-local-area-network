from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    # Server settings
    HOST: str = Field("0.0.0.0", description="Host to bind the server to")
    PORT: int = Field(8000, description="Port to bind the server to")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
