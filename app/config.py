from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Task Management API"
    app_version: str = "0.1.0"
    debug: bool = True
    
    database_url: str = "sqlite:///./task_api.db"
    test_database_url: str = "sqlite:///./test_task_api.db"
    
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()