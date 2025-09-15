"""Factory for creating storage service implementations."""

from typing import Dict, Any, Optional
from ..interfaces.storage import StorageInterface, StorageType, StorageError


class StorageFactory:
    """Factory for creating storage service instances."""
    
    _implementations: Dict[StorageType, type] = {}
    
    @classmethod
    def create_storage(
        cls, 
        storage_type: StorageType, 
        config: Dict[str, Any]
    ) -> StorageInterface:
        """Create storage service instance."""
        # Lazy import implementations to avoid circular imports
        if storage_type not in cls._implementations:
            if storage_type == StorageType.LOCAL:
                from ..implementations.storage.local import LocalStorage
                cls._implementations[storage_type] = LocalStorage
            elif storage_type == StorageType.MINIO:
                # TODO: Implement MinioStorage
                raise StorageError(f"MinioStorage not yet implemented")
            elif storage_type == StorageType.S3:
                # TODO: Implement S3Storage
                raise StorageError(f"S3Storage not yet implemented")
            else:
                raise StorageError(f"Unsupported storage type: {storage_type}")
        
        implementation_class = cls._implementations[storage_type]
        return implementation_class(config)
    
    @classmethod
    def create_from_env(cls, env_config: Dict[str, str]) -> StorageInterface:
        """Create storage service from environment configuration."""
        storage_type_str = env_config.get("STORAGE_TYPE", "minio")
        
        try:
            storage_type = StorageType(storage_type_str)
        except ValueError:
            raise StorageError(f"Invalid storage type: {storage_type_str}")
        
        config = cls._build_config(storage_type, env_config)
        return cls.create_storage(storage_type, config)
    
    @classmethod
    def _build_config(cls, storage_type: StorageType, env_config: Dict[str, str]) -> Dict[str, Any]:
        """Build configuration for storage type."""
        if storage_type == StorageType.MINIO:
            return {
                "endpoint": env_config.get("MINIO_ENDPOINT", "localhost:9000"),
                "access_key": env_config.get("MINIO_ACCESS_KEY", "minioadmin"),
                "secret_key": env_config.get("MINIO_SECRET_KEY", "minioadmin"),
                "bucket": env_config.get("MINIO_BUCKET", "legal-sim-evidence"),
                "secure": env_config.get("MINIO_SECURE", "false").lower() == "true",
            }
        
        elif storage_type == StorageType.S3:
            return {
                "access_key_id": env_config.get("AWS_ACCESS_KEY_ID"),
                "secret_access_key": env_config.get("AWS_SECRET_ACCESS_KEY"),
                "region": env_config.get("AWS_REGION", "us-east-1"),
                "bucket": env_config.get("S3_BUCKET", "legal-sim-evidence"),
            }
        
        elif storage_type == StorageType.LOCAL:
            return {
                "base_path": env_config.get("LOCAL_STORAGE_PATH", "/tmp/legal-sim-storage"),
            }
        
        else:
            raise StorageError(f"Configuration not implemented for {storage_type}")
    
    @classmethod
    def register_implementation(
        cls, 
        storage_type: StorageType, 
        implementation_class: type
    ) -> None:
        """Register custom storage implementation."""
        cls._implementations[storage_type] = implementation_class
