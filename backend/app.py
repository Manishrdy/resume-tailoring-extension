"""
Resume Tailor API - Main Application Entry Point

A FastAPI backend service that processes job descriptions and tailors resumes
using Google's Gemini AI.

IMPORTANT:
- All logging must go through the centralized logger service
- Resume path must ONLY be accessed via config.settings.resume_path
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import centralized logger FIRST
from logger import setup_logging, get_logger

# Import configuration
from config import settings

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
    InvalidJobDescriptionError,
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
    4. Generates PDF and/or DOCX output files (Phase 4)
    
    Args:
        request: TailorRequest containing job description and options
        
    Returns:
        TailorResponse: Status and paths to generated files
    """
    import time
    start_time = time.time()
    
    logger.info(
        f"Tailor request received",
        extra={
            "job_title": request.job_title or "Unknown",
            "company": request.company or "Unknown",
            "jd_length": len(request.job_description),
            "output_formats": request.output_formats,
        },
    )
    
    # Import services
    from services.resume_parser import ResumeParser
    from services.gemini_service import GeminiService
    
    try:
        # Step 1: Parse the resume (path accessed via config)
        logger.info(f"Parsing resume: {settings.resume_path}")
        parser = ResumeParser(settings.resume_path)
        parsed_resume = parser.parse()
        
        logger.info(
            f"Resume parsed: {parsed_resume.word_count} words, "
            f"{len(parsed_resume.skills)} skills found"
        )
        
        # Step 2: Initialize Gemini service and tailor the resume
        logger.info("Initializing Gemini service...")
        gemini = GeminiService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        
        # Step 3: Tailor the resume using AI
        logger.info("Tailoring resume with Gemini AI...")
        tailored = gemini.tailor_resume(
            resume_text=parsed_resume.raw_text,
            job_description=request.job_description,
            job_title=request.job_title,
            company=request.company,
            emphasis_keywords=request.emphasis_keywords,
        )
        
        # Step 4: Generate documents
        logger.info(f"Generating documents in formats: {request.output_formats}")
        from services.document_gen import DocumentGenerator
        
        doc_generator = DocumentGenerator(settings.output_dir)
        
        # Get candidate name from parsed resume
        candidate_name = None
        if parsed_resume.contact_info and parsed_resume.contact_info.name:
            candidate_name = parsed_resume.contact_info.name
        
        generated_docs = doc_generator.generate(
            content=tailored.tailored_text,
            formats=request.output_formats,
            job_title=request.job_title,
            company=request.company,
            candidate_name=candidate_name,
        )
        
        # Convert to response model
        from models import GeneratedFile
        files_generated = [
            GeneratedFile(
                filename=doc.filename,
                format=doc.format,
                path=str(doc.path),
                size_bytes=doc.size_bytes,
                download_url=f"/download/{doc.filename}",
            )
            for doc in generated_docs
        ]
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        response = TailorResponse(
            status="success",
            message=tailored.summary or "Resume tailored successfully",
            job_title=request.job_title,
            company=request.company,
            files_generated=files_generated,
            output_formats=request.output_formats,
            keywords_matched=tailored.matched_keywords,
            processing_time_ms=processing_time_ms,
            tailored_content=tailored.tailored_text,
            suggestions=tailored.suggestions,
            ats_score=tailored.ats_score,
        )
        
        logger.info(
            f"Tailor request completed in {processing_time_ms}ms. "
            f"Generated {len(files_generated)} files, "
            f"Matched {len(tailored.matched_keywords)} keywords, "
            f"ATS score: {tailored.ats_score}"
        )
        
        return response
        
    except FileNotFoundError as e:
        logger.error(f"Resume file not found: {e}")
        raise ResumeNotFoundError(
            filename=settings.resume_filename,
            path=str(settings.resume_path)
        )
    except Exception as e:
        logger.exception(f"Error tailoring resume: {e}")
        raise


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


@app.get(
    "/resume/parse",
    tags=["Resume"],
    summary="Parse Resume",
    description="Parse the configured resume and return structured content",
)
async def parse_resume():
    """
    Parse the configured resume file and return structured data.
    
    This endpoint extracts:
    - Contact information
    - Skills
    - Resume sections
    - Word count
    
    Returns:
        dict: Parsed resume data
    """
    logger.info("Resume parse requested")
    
    from services.resume_parser import ResumeParser
    
    try:
        parser = ResumeParser(settings.resume_path)
        parsed = parser.parse()
        
        return {
            "status": "success",
            "data": parsed.to_dict(),
            "raw_text_preview": parsed.raw_text[:500] + "..." if len(parsed.raw_text) > 500 else parsed.raw_text,
        }
        
    except FileNotFoundError as e:
        logger.error(f"Resume file not found: {e}")
        raise ResumeNotFoundError(
            filename=settings.resume_filename,
            path=str(settings.resume_path)
        )
    except Exception as e:
        logger.exception(f"Error parsing resume: {e}")
        raise


@app.post(
    "/job/extract",
    tags=["Job"],
    summary="Extract Job Details",
    description="Extract structured information from a job description",
)
async def extract_job_details(job_description: str):
    """
    Extract structured information from a job description.
    
    Uses Gemini AI to parse the job description and extract:
    - Job title and company
    - Required and preferred skills
    - Responsibilities and requirements
    - Benefits and salary information
    
    Args:
        job_description: Raw job description text
        
    Returns:
        dict: Extracted job details
    """
    logger.info("Job extraction requested")
    
    from services.gemini_service import GeminiService
    
    if len(job_description) < 50:
        raise InvalidJobDescriptionError("Job description too short (minimum 50 characters)")
    
    try:
        gemini = GeminiService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        
        details = gemini.extract_job_details(job_description)
        
        return {
            "status": "success",
            "data": details.to_dict(),
        }
        
    except Exception as e:
        logger.exception(f"Error extracting job details: {e}")
        raise


@app.get(
    "/gemini/test",
    tags=["Configuration"],
    summary="Test Gemini Connection",
    description="Test the connection to Gemini API",
)
async def test_gemini():
    """
    Test the Gemini API connection.
    
    Returns:
        dict: Connection test result
    """
    logger.info("Gemini connection test requested")
    
    from services.gemini_service import GeminiService
    
    if not settings.gemini_api_key:
        return {
            "status": "error",
            "message": "GEMINI_API_KEY not configured",
            "connected": False,
        }
    
    try:
        gemini = GeminiService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
        
        connected = gemini.test_connection()
        
        return {
            "status": "success" if connected else "error",
            "message": "Connection successful" if connected else "Connection failed",
            "connected": connected,
            "model": settings.gemini_model,
        }
        
    except Exception as e:
        logger.error(f"Gemini connection test failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "connected": False,
        }


@app.get(
    "/download/{filename}",
    tags=["Files"],
    summary="Download Generated File",
    description="Download a generated resume file",
)
async def download_file(filename: str):
    """
    Download a generated resume file.
    
    Args:
        filename: Name of the file to download
        
    Returns:
        FileResponse: The requested file
    """
    from fastapi.responses import FileResponse
    
    logger.info(f"Download requested: {filename}")
    
    file_path = settings.output_dir / filename
    
    if not file_path.exists():
        logger.warning(f"File not found: {filename}")
        raise ResumeNotFoundError(filename=filename, path=str(file_path))
    
    # Determine media type
    media_type = "application/octet-stream"
    if filename.endswith('.pdf'):
        media_type = "application/pdf"
    elif filename.endswith('.docx'):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@app.get(
    "/files",
    tags=["Files"],
    summary="List Generated Files",
    description="List all generated resume files",
)
async def list_files():
    """
    List all generated resume files.
    
    Returns:
        dict: List of generated files
    """
    logger.debug("File listing requested")
    
    from services.document_gen import DocumentGenerator
    
    doc_generator = DocumentGenerator(settings.output_dir)
    files = doc_generator.list_generated_files()
    
    return {
        "status": "success",
        "count": len(files),
        "files": files,
    }


@app.delete(
    "/files/cleanup",
    tags=["Files"],
    summary="Cleanup Old Files",
    description="Remove old generated files",
)
async def cleanup_files(keep_count: int = 10):
    """
    Remove old generated files, keeping only recent ones.
    
    Args:
        keep_count: Number of files to keep (default: 10)
        
    Returns:
        dict: Cleanup result
    """
    logger.info(f"File cleanup requested, keeping {keep_count} files")
    
    from services.document_gen import DocumentGenerator
    
    doc_generator = DocumentGenerator(settings.output_dir)
    deleted = doc_generator.cleanup_old_files(keep_count)
    
    return {
        "status": "success",
        "deleted_count": deleted,
        "message": f"Deleted {deleted} old files",
    }


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
