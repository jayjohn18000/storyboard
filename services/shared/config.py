"""
Shared configuration module for Legal Simulation Platform.

This module provides centralized configuration management for all services,
including service discovery, environment validation, and common settings.
"""

import os
from typing import Literal, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic.networks import AnyUrl


class ServiceConfig(BaseSettings):
    """Configuration for service URLs and discovery."""
    
    # Service URLs
    api_gateway_url: str = Field(default="http://localhost:8000")
    evidence_url: str = Field(default="http://localhost:8001")
    storyboard_url: str = Field(default="http://localhost:8002")
    timeline_url: str = Field(default="http://localhost:8003")
    render_url: str = Field(default="http://localhost:8004")
    
    # Service ports (for validation)
    api_gateway_port: int = Field(default=8000)
    evidence_port: int = Field(default=8001)
    storyboard_port: int = Field(default=8002)
    timeline_port: int = Field(default=8003)
    render_port: int = Field(default=8004)
    
    # Service names
    api_gateway_name: str = Field(default="api-gateway")
    evidence_name: str = Field(default="evidence-processor")
    storyboard_name: str = Field(default="storyboard-service")
    timeline_name: str = Field(default="timeline-compiler")
    render_name: str = Field(default="render-orchestrator")
    
    @field_validator('api_gateway_port', 'evidence_port', 'storyboard_port', 'timeline_port', 'render_port')
    @classmethod
    def validate_ports(cls, v):
        """Validate that ports are in the expected range."""
        if not (8000 <= v <= 8004):
            raise ValueError(f"Port {v} must be between 8000 and 8004")
        return v
    
    @field_validator('api_gateway_url', 'evidence_url', 'storyboard_url', 'timeline_url', 'render_url')
    @classmethod
    def validate_urls(cls, v):
        """Validate that URLs are properly formatted."""
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {v}")
            return v
        except Exception as e:
            raise ValueError(f"Invalid URL format: {v}") from e


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    database_url: str = Field(default="postgresql://legal_sim:password@localhost:5432/legal_sim")
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("Database URL must be a PostgreSQL connection string")
        return v


class RedisConfig(BaseSettings):
    """Redis configuration."""
    
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: Optional[str] = Field(default=None)
    
    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, v):
        """Validate Redis URL format."""
        if not v.startswith('redis://'):
            raise ValueError("Redis URL must start with redis://")
        return v


class SecurityConfig(BaseSettings):
    """Security configuration."""
    
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    encryption_key: str = Field(default="your-encryption-key-change-in-production")
    signing_key: str = Field(default="your-signing-key-change-in-production")


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration."""
    
    otel_exporter_otlp_endpoint: Optional[str] = Field(default=None)
    otel_service_name: str = Field(default="legal-sim")
    otel_service_version: str = Field(default="0.1.0")
    log_level: str = Field(default="INFO")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class AppConfig(BaseSettings):
    """Application configuration."""
    
    app_name: str = Field(default="legal-sim")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="mvp")
    mode: str = Field(default="demonstrative")
    debug: bool = Field(default=False)
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ['mvp', 'production', 'enterprise']
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Validate mode setting."""
        valid_modes = ['sandbox', 'demonstrative']
        if v not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        return v


class Config:
    """Main configuration class that combines all configuration sections."""
    
    def __init__(self):
        self.service = ServiceConfig()
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.app = AppConfig()
    
    def get_service_url(self, service_name: Literal["evidence", "storyboard", "timeline", "render"]) -> AnyUrl:
        """
        Get the URL for a specific service.
        
        Args:
            service_name: Name of the service to get URL for
            
        Returns:
            Service URL as AnyUrl
            
        Raises:
            ValueError: If service_name is not recognized
        """
        service_urls = {
            "evidence": self.service.evidence_url,
            "storyboard": self.service.storyboard_url,
            "timeline": self.service.timeline_url,
            "render": self.service.render_url,
        }
        
        if service_name not in service_urls:
            raise ValueError(f"Unknown service: {service_name}. Must be one of {list(service_urls.keys())}")
        
        return AnyUrl(service_urls[service_name])
    
    def get_service_name(self, service_name: Literal["evidence", "storyboard", "timeline", "render"]) -> str:
        """
        Get the display name for a specific service.
        
        Args:
            service_name: Name of the service to get display name for
            
        Returns:
            Service display name
            
        Raises:
            ValueError: If service_name is not recognized
        """
        service_names = {
            "evidence": self.service.evidence_name,
            "storyboard": self.service.storyboard_name,
            "timeline": self.service.timeline_name,
            "render": self.service.render_name,
        }
        
        if service_name not in service_names:
            raise ValueError(f"Unknown service: {service_name}. Must be one of {list(service_names.keys())}")
        
        return service_names[service_name]
    
    def is_sandbox_mode(self) -> bool:
        """Check if the application is running in sandbox mode."""
        return self.app.mode == "sandbox"
    
    def is_demonstrative_mode(self) -> bool:
        """Check if the application is running in demonstrative mode."""
        return self.app.mode == "demonstrative"
    
    def is_debug_mode(self) -> bool:
        """Check if the application is running in debug mode."""
        return self.app.debug


# Global configuration instance
config = Config()


def get_service_url(service_name: Literal["evidence", "storyboard", "timeline", "render"]) -> AnyUrl:
    """
    Convenience function to get service URL.
    
    Args:
        service_name: Name of the service to get URL for
        
    Returns:
        Service URL as AnyUrl
    """
    return config.get_service_url(service_name)


def get_service_name(service_name: Literal["evidence", "storyboard", "timeline", "render"]) -> str:
    """
    Convenience function to get service name.
    
    Args:
        service_name: Name of the service to get display name for
        
    Returns:
        Service display name
    """
    return config.get_service_name(service_name)
