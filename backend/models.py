"""
Pydantic Models

Data models for API request/response validation and serialization.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# Request Models
class TailorRequest(BaseModel):
    """Request model for resume tailoring endpoint."""
    
    job_description: str = Field(
        ...,
        min_length=50,
        max_length=50000,
        description="The job description text to tailor the resume for",
        examples=["We are looking for a Senior Software Engineer with 5+ years of experience..."],
    )
    
    job_title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Job title (optional, will be extracted from JD if not provided)",
        examples=["Senior Software Engineer"],
    )
    
    company: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Company name (optional)",
        examples=["Google", "Microsoft"],
    )
    
    job_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="URL of the job posting",
        examples=["https://careers.google.com/jobs/123"],
    )
    
    output_formats: list[Literal["pdf", "docx"]] = Field(
        default=["pdf", "docx"],
        description="Desired output formats for the tailored resume",
    )
    
    emphasis_keywords: Optional[list[str]] = Field(
        default=None,
        max_length=20,
        description="Additional keywords to emphasize in the tailored resume",
        examples=[["Python", "AWS", "Leadership"]],
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_description": "We are seeking a Senior Software Engineer to join our team. Requirements: 5+ years Python experience, AWS knowledge, strong communication skills...",
                "job_title": "Senior Software Engineer",
                "company": "TechCorp Inc.",
                "output_formats": ["pdf", "docx"],
            }
        }


# Response Models
class GeneratedFile(BaseModel):
    """Information about a generated file."""
    
    filename: str = Field(
        description="Name of the generated file",
    )
    
    format: Literal["pdf", "docx"] = Field(
        description="File format",
    )
    
    path: str = Field(
        description="Full path to the generated file",
    )
    
    size_bytes: int = Field(
        description="File size in bytes",
    )
    
    download_url: Optional[str] = Field(
        default=None,
        description="URL to download the file (if applicable)",
    )


class TailorResponse(BaseModel):
    """Response model for successful resume tailoring."""
    
    status: Literal["success", "partial", "pending"] = Field(
        description="Status of the tailoring operation",
    )
    
    message: str = Field(
        description="Human-readable status message",
    )
    
    job_title: Optional[str] = Field(
        default=None,
        description="Extracted or provided job title",
    )
    
    company: Optional[str] = Field(
        default=None,
        description="Extracted or provided company name",
    )
    
    files_generated: list[GeneratedFile] = Field(
        default_factory=list,
        description="List of generated files",
    )
    
    output_formats: list[str] = Field(
        description="Formats that were requested",
    )
    
    keywords_matched: Optional[list[str]] = Field(
        default=None,
        description="Keywords from JD that were matched/emphasized",
    )
    
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Time taken to process the request in milliseconds",
    )
    
    tailored_content: Optional[str] = Field(
        default=None,
        description="The AI-tailored resume content",
    )
    
    suggestions: Optional[list[str]] = Field(
        default=None,
        description="AI suggestions for improving the resume",
    )
    
    ats_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Estimated ATS compatibility score (0-100)",
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the response was created",
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        description="Overall health status of the service",
    )
    
    version: str = Field(
        description="API version",
    )
    
    checks: dict[str, str] = Field(
        description="Individual component health checks",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the health check",
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(
        description="Error code for programmatic handling",
        examples=["VALIDATION_ERROR", "RESUME_NOT_FOUND", "GEMINI_API_ERROR"],
    )
    
    message: str = Field(
        description="Human-readable error message",
    )
    
    details: Optional[dict] = Field(
        default=None,
        description="Additional error details (only in debug mode)",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the error occurred",
    )
