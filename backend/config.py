"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Repository settings
    repository_base_path: str = "/app/repositories"
    
    # AWS settings
    aws_profile: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    
    # Oracle database settings
    oracle_jdbc_url: Optional[str] = None
    oracle_username: Optional[str] = None
    oracle_password: Optional[str] = None
    oracle_schema: Optional[str] = None
    
    # Jira settings
    jira_base_url: Optional[str] = None
    jira_pat: Optional[str] = None
    jira_username: Optional[str] = None
    
    # Application settings
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"