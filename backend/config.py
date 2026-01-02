"""
Configuration Management

Centralized configuration using Pydantic Settings for type-safe
environment variable handling with validation.

IMPORTANT: All file paths, especially resume paths, must be accessed
through this configuration module. Never hardcode paths.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigurationError(Exception):
    """Raised when there's a configuration problem."""
    pass


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    Resume path is ONLY accessible through this configuration.
    
    NOTE: Validation is deferred to startup via validate_for_startup() method.
    This allows the app to load and show helpful error messages.
    """
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ===========================================
    # API Configuration
    # ===========================================
    
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key for AI processing",
    )
    
    gemini_model: str = Field(
        default="gemini-1.5-flash",
        description="Gemini model to use for content generation",
    )
    
    # ===========================================
    # Resume Configuration (via .env ONLY)
    # ===========================================
    
    resume_filename: str = Field(
        default="",
        description="Filename of the base resume in the resume directory",
    )
    
    resume_dir_name: str = Field(
        default="resume",
        description="Directory name where resumes are stored (relative to base_dir)",
    )
    
    # ===========================================
    # Server Configuration
    # ===========================================
    
    host: str = Field(
        default="127.0.0.1",
        description="Host to bind the server to",
    )
    
    port: int = Field(
        default=5000,
        ge=1,
        le=65535,
        description="Port to run the server on",
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode with auto-reload and verbose errors",
    )
    
    # ===========================================
    # Logging Configuration
    # ===========================================
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    
    log_json: bool = Field(
        default=False,
        description="Enable JSON formatted logs for production",
    )
    
    # ===========================================
    # Path Configuration
    # ===========================================
    
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent,
        description="Base directory of the project",
    )
    
    # ===========================================
    # Validators (lightweight, non-blocking)
    # ===========================================
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            return "INFO"  # Default to INFO if invalid
        return v_upper
    
    @field_validator("resume_filename")
    @classmethod
    def clean_resume_filename(cls, v: str) -> str:
        """Clean resume filename (strip whitespace)."""
        return v.strip() if v else ""
    
    # ===========================================
    # Computed Properties (Path Access)
    # ===========================================
    
    @property
    def resume_dir(self) -> Path:
        """
        Path to the resume storage directory.
        
        Configured via .env: RESUME_DIR_NAME (default: 'resume')
        """
        return self.base_dir / self.resume_dir_name
    
    @property
    def resume_path(self) -> Path:
        """
        Full path to the resume file.
        
        This is the ONLY way to access the resume path.
        Configured via .env: RESUME_FILENAME
        
        Returns:
            Path: Absolute path to the resume file
        """
        return self.resume_dir / self.resume_filename
    
    @property
    def output_dir(self) -> Path:
        """Path to the output directory for generated files."""
        return self.base_dir / "backend" / "outputs"
    
    @property
    def logs_dir(self) -> Path:
        """Path to the logs directory."""
        return self.base_dir / "backend" / "logs"
    
    # ===========================================
    # Helper Methods
    # ===========================================
    
    def get_resume_info(self) -> dict:
        """
        Get resume file information.
        
        Returns:
            dict: Resume file metadata
        """
        if not self.resume_filename:
            return {
                "filename": None,
                "path": None,
                "exists": False,
                "format": None,
                "size_bytes": None,
            }
        
        path = self.resume_path
        exists = path.exists()
        return {
            "filename": self.resume_filename,
            "path": str(path),
            "exists": exists,
            "format": path.suffix.lower() if exists else None,
            "size_bytes": path.stat().st_size if exists else None,
        }
    
    def validate_for_startup(self) -> list[str]:
        """
        Validate all required configuration for startup.
        
        Call this during application startup to get a list of errors.
        
        Returns:
            list[str]: List of configuration errors (empty if valid)
        """
        errors = []
        
        # Check resume filename is set
        if not self.resume_filename:
            errors.append(
                "RESUME_FILENAME is not set in .env file.\n"
                "  → Add: RESUME_FILENAME=your_resume.pdf"
            )
        else:
            # Check resume file exists
            if not self.resume_path.exists():
                errors.append(
                    f"Resume file not found: {self.resume_path}\n"
                    f"  → Place your resume in: {self.resume_dir}/\n"
                    f"  → Or update RESUME_FILENAME in .env"
                )
            else:
                # Check file extension
                valid_extensions = {".pdf", ".docx", ".doc"}
                if self.resume_path.suffix.lower() not in valid_extensions:
                    errors.append(
                        f"Invalid resume format: {self.resume_path.suffix}\n"
                        f"  → Supported formats: {', '.join(valid_extensions)}"
                    )
        
        # Warning for Gemini API key (not blocking)
        if not self.gemini_api_key:
            errors.append(
                "GEMINI_API_KEY is not set in .env file.\n"
                "  → AI features will not work without it.\n"
                "  → Get your key at: https://aistudio.google.com/app/apikey"
            )
        
        return errors
    
    def validate_or_raise(self) -> None:
        """
        Validate configuration and raise if invalid.
        
        Raises:
            ConfigurationError: If required configuration is missing
        """
        errors = self.validate_for_startup()
        
        # Filter to only critical errors (not warnings like missing API key)
        critical_errors = [e for e in errors if "RESUME_FILENAME" in e or "not found" in e or "Invalid resume" in e]
        
        if critical_errors:
            error_msg = "Configuration errors:\n\n" + "\n\n".join(critical_errors)
            raise ConfigurationError(error_msg)
    
    def get_validation_status(self) -> dict[str, bool]:
        """
        Get validation status for each component.
        
        Returns:
            dict: Validation status for each component
        """
        return {
            "gemini_api_key": bool(self.gemini_api_key),
            "resume_filename_set": bool(self.resume_filename),
            "resume_file_exists": self.resume_path.exists() if self.resume_filename else False,
            "output_dir": self.output_dir.exists() or True,  # Will be created
            "logs_dir": self.logs_dir.exists() or True,  # Will be created
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once
    and reused across the application.
    
    NOTE: This does NOT validate configuration. Call settings.validate_for_startup()
    or settings.validate_or_raise() during app startup.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


def reload_settings() -> Settings:
    """
    Force reload settings from .env file.
    
    Clears the cache and reloads configuration.
    Use sparingly - mainly for testing.
    
    Returns:
        Settings: Fresh settings instance
    """
    get_settings.cache_clear()
    return get_settings()


# Global settings instance for easy import
# Usage: from config import settings
settings = get_settings()
