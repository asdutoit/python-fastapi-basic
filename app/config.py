from pydantic_settings import BaseSettings
from typing import List, Union
import json


class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Task Management API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database Settings
    database_url: str = "sqlite:///./task_api.db"
    test_database_url: str = "sqlite:///./test_task_api.db"
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Settings
    cors_origins: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Feature Flags
    enable_registration: bool = True
    enable_password_reset: bool = False
    
    # PostgreSQL specific settings
    postgres_db: str = "taskapi"
    postgres_user: str = "taskapi_user"
    postgres_password: str = "secure_password_change_me"
    
    # Apigee Integration Settings
    apigee_enabled: bool = False
    apigee_proxy_name: str = "task-management-api"
    apigee_base_path: str = "/api/v1"
    apigee_org: str = ""
    apigee_env: str = "test"
    target_backend_url: str = "https://your-backend-url.com"
    
    # API Gateway Headers
    trust_proxy_headers: bool = False
    forwarded_allow_ips: str = "*"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string or return list"""
        if isinstance(self.cors_origins, str):
            try:
                return json.loads(self.cors_origins)
            except json.JSONDecodeError:
                return [self.cors_origins]
        return self.cors_origins


settings = Settings()