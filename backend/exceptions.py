"""
Custom Exceptions

Application-specific exception classes for structured error handling.
"""

from typing import Optional

# Import ConfigurationError from config to avoid duplication
from config import ConfigurationError


class ResumeTailorException(Exception):
    """Base exception for all Resume Tailor application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ResumeNotFoundError(ResumeTailorException):
    """Raised when the resume file cannot be found."""
    
    def __init__(self, filename: str, path: str):
        super().__init__(
            message=f"Resume file not found: {filename}",
            error_code="RESUME_NOT_FOUND",
            status_code=404,
            details={"filename": filename, "expected_path": path},
        )


class ResumeParseError(ResumeTailorException):
    """Raised when the resume file cannot be parsed."""
    
    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to parse resume: {reason}",
            error_code="RESUME_PARSE_ERROR",
            status_code=422,
            details={"filename": filename, "reason": reason},
        )


class GeminiAPIError(ResumeTailorException):
    """Raised when Gemini API call fails."""
    
    def __init__(self, message: str, api_error: Optional[str] = None):
        super().__init__(
            message=f"Gemini API error: {message}",
            error_code="GEMINI_API_ERROR",
            status_code=503,
            details={"api_error": api_error} if api_error else None,
        )


class GeminiRateLimitError(GeminiAPIError):
    """Raised when Gemini API rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            message="Gemini API rate limit exceeded. Please try again later.",
            api_error="RATE_LIMIT_EXCEEDED",
        )
        self.error_code = "GEMINI_RATE_LIMIT"
        self.status_code = 429
        if retry_after:
            self.details = {"retry_after_seconds": retry_after}


class DocumentGenerationError(ResumeTailorException):
    """Raised when document generation fails."""
    
    def __init__(self, format: str, reason: str):
        super().__init__(
            message=f"Failed to generate {format.upper()} document: {reason}",
            error_code="DOCUMENT_GENERATION_ERROR",
            status_code=500,
            details={"format": format, "reason": reason},
        )


class InvalidJobDescriptionError(ResumeTailorException):
    """Raised when the job description is invalid or too short."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid job description: {reason}",
            error_code="INVALID_JOB_DESCRIPTION",
            status_code=400,
            details={"reason": reason},
        )


# Re-export ConfigurationError from config for convenience
__all__ = [
    "ResumeTailorException",
    "ResumeNotFoundError",
    "ResumeParseError",
    "GeminiAPIError",
    "GeminiRateLimitError",
    "DocumentGenerationError",
    "InvalidJobDescriptionError",
    "ConfigurationError",
]
