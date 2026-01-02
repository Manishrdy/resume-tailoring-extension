from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import centralized logger FIRST
from logger import setup_logging, get_logger

# Import configuration
from config import settings
print("Loaded resume filename:", settings.resume_filename)
print("Resume path:", settings.resume_path)
print("Exists:", settings.resume_path.exists())

# Initialize logging before anything else
setup_logging(
    log_dir=settings.logs_dir,
    debug=settings.debug,
    enable_json=settings.log_json,
)

# Now get logger for this module
logger = get_logger(__name__)

# Import models and exceptions after logging is set up
from models import (
    TailorRequest,
    TailorResponse,
    HealthResponse,
    ErrorResponse,
)
from exceptions import (
    ResumeTailorException,
    ResumeNotFoundError,
    GeminiAPIError,
    DocumentGenerationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Resume Tailor API...")
    logger.info("=" * 60)
    
    # Validate configuration
    _validate_startup_config()
    
    # Create necessary directories
    _ensure_directories()
    
    logger.info("Resume Tailor API started successfully")
    logger.info(f"Server running at http://{settings.host}:{settings.port}")
    logger.info(f"API Docs available at http://{settings.host}:{settings.port}/docs")
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down Resume Tailor API...")
    logger.info("=" * 60)


def _validate_startup_config() -> None:
    """
    Validate required configuration on startup.
    
    All resume path access goes through settings.resume_path
    Uses deferred validation from config module.
    """
    logger.info("Validating configuration...")
    
    # Get all validation errors/warnings from config
    validation_errors = settings.validate_for_startup()
    
    # Separate critical errors from warnings
    critical_errors = []
    warnings = []
    
    for error in validation_errors:
        if "GEMINI_API_KEY" in error:
            warnings.append(error)
        else:
            critical_errors.append(error)
    
    # Log warnings (non-blocking)
    for warning in warnings:
        logger.warning(warning.replace("\n", " | "))
    
    # Log current configuration status
    if settings.gemini_api_key:
        logger.info("Gemini API key: configured")
    
    if settings.resume_filename:
        resume_info = settings.get_resume_info()
        if resume_info["exists"]:
            logger.info(f"Resume file: {resume_info['filename']}")
            logger.info(f"Resume format: {resume_info['format']}")
            logger.info(f"Resume size: {resume_info['size_bytes']} bytes")
    
    # Log configuration summary
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Gemini model: {settings.gemini_model}")
    
    # Fail on critical errors
    if critical_errors:
        logger.error("=" * 60)
        logger.error("CONFIGURATION ERRORS - Please fix before running:")
        logger.error("=" * 60)
        for error in critical_errors:
            for line in error.split("\n"):
                logger.error(line)
        logger.error("=" * 60)
        raise RuntimeError(
            "\n\nConfiguration errors detected!\n\n" + 
            "\n\n".join(critical_errors) +
            "\n\nPlease fix the above errors in your .env file and try again."
        )
    
    logger.info("Configuration validated successfully")


def _ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    directories = [
        ("outputs", settings.output_dir),
        ("logs", settings.logs_dir),
    ]
    
    for name, directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured {name} directory exists: {directory}")


# Initialize FastAPI application
app = FastAPI(
    title="Resume Tailor API",
    description="AI-powered resume tailoring service using Google Gemini",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "http://localhost:*",
        "http://127.0.0.1:*",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# ===========================================
# Exception Handlers
# ===========================================

@app.exception_handler(ResumeTailorException)
async def resume_tailor_exception_handler(request, exc: ResumeTailorException):
    """Handle custom application exceptions."""
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"error": str(exc)} if settings.debug else None,
        ).model_dump(),
    )


# ===========================================
# API Endpoints
# ===========================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running and all dependencies are available",
)
async def health_check() -> HealthResponse:
    """
    Perform health check on the API and its dependencies.
    
    Returns:
        HealthResponse: Current health status of the service
    """
    logger.debug("Health check requested")
    
    # Access resume info through config
    resume_info = settings.get_resume_info()
    resume_exists = resume_info["exists"]
    gemini_configured = bool(settings.gemini_api_key)
    
    is_healthy = resume_exists and gemini_configured
    
    checks = {
        "resume_file": "ok" if resume_exists else "missing",
        "gemini_api": "configured" if gemini_configured else "not_configured",
        "output_directory": "ok" if settings.output_dir.exists() else "missing",
    }
    
    status_str = "healthy" if is_healthy else "degraded"
    logger.info(f"Health check: {status_str}", extra={"checks": checks})
    
    return HealthResponse(
        status=status_str,
        version="1.0.0",
        checks=checks,
    )


@app.post(
    "/tailor",
    response_model=TailorResponse,
    tags=["Resume"],
    summary="Tailor Resume",
    description="Process a job description and generate a tailored resume",
    responses={
        200: {"description": "Resume tailored successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Resume not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Gemini API unavailable"},
    },
)
async def tailor_resume(request: TailorRequest) -> TailorResponse:
    """
    Tailor the stored resume based on the provided job description.
    
    This endpoint:
    1. Reads the base resume from storage (via config.settings.resume_path)
    2. Analyzes the job description
    3. Uses Gemini AI to tailor the resume
    4. Generates PDF and/or DOCX output files
    
    Args:
        request: TailorRequest containing job description and options
        
    Returns:
        TailorResponse: Status and paths to generated files
    """
    logger.info(
        f"Tailor request received",
        extra={
            "job_title": request.job_title or "Unknown",
            "company": request.company or "Unknown",
            "jd_length": len(request.job_description),
            "output_formats": request.output_formats,
        },
    )
    
    # Log resume being used (path accessed via config)
    logger.debug(f"Using resume: {settings.resume_path}")
    
    # Phase 1: Return placeholder response
    # Actual implementation will be added in subsequent phases
    
    response = TailorResponse(
        status="success",
        message="Resume tailoring endpoint ready. Full implementation coming in Phase 2-4.",
        job_title=request.job_title,
        company=request.company,
        files_generated=[],
        output_formats=request.output_formats,
    )
    
    logger.info("Tailor request completed (placeholder response)")
    
    return response


@app.get(
    "/config",
    tags=["Configuration"],
    summary="Get Current Configuration",
    description="Retrieve non-sensitive configuration details",
)
async def get_config():
    """
    Get current configuration (non-sensitive values only).
    
    Returns:
        dict: Current configuration settings
    """
    logger.debug("Configuration requested")
    
    # Get resume info through config
    resume_info = settings.get_resume_info()
    
    return {
        "resume": {
            "filename": resume_info["filename"],
            "format": resume_info["format"],
            "exists": resume_info["exists"],
        },
        "output_directory": str(settings.output_dir),
        "supported_formats": ["pdf", "docx"],
        "gemini_model": settings.gemini_model,
        "debug_mode": settings.debug,
        "log_level": settings.log_level,
    }


@app.get(
    "/resume/info",
    tags=["Resume"],
    summary="Get Resume Information",
    description="Get information about the configured resume file",
)
async def get_resume_info():
    """
    Get information about the currently configured resume.
    
    Resume path is accessed ONLY through settings.
    
    Returns:
        dict: Resume file information
    """
    logger.debug("Resume info requested")
    
    # All resume access through config
    info = settings.get_resume_info()
    
    logger.info(f"Resume info: {info['filename']} (exists: {info['exists']})")
    
    return info


# ===========================================
# Main Entry Point
# ===========================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
