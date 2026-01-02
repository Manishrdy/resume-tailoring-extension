"""
Document Generator Service

Handles generation of PDF and DOCX documents from tailored resume content.
Full implementation in Phase 4.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from logger import get_logger

# Module logger
logger = get_logger(__name__)


@dataclass
class GeneratedDocument:
    """Information about a generated document."""
    
    path: Path
    format: Literal["pdf", "docx"]
    filename: str
    size_bytes: int
    created_at: datetime


class DocumentGenerator:
    """
    Service for generating resume documents.
    
    Supports PDF and DOCX output formats with professional formatting.
    
    Usage:
        from config import settings
        generator = DocumentGenerator(settings.output_dir)
        files = generator.generate(content, ["pdf", "docx"])
    """
    
    SUPPORTED_FORMATS = {"pdf", "docx"}
    
    def __init__(self, output_dir: Path):
        """
        Initialize the document generator.
        
        Args:
            output_dir: Directory to save generated documents (from config.settings.output_dir)
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing DocumentGenerator with output_dir: {output_dir}")
    
    def generate(
        self,
        content: str,
        formats: list[Literal["pdf", "docx"]],
        base_filename: Optional[str] = None,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
    ) -> list[GeneratedDocument]:
        """
        Generate resume documents in specified formats.
        
        Args:
            content: Tailored resume content
            formats: List of output formats to generate
            base_filename: Base name for output files
            job_title: Job title for filename
            company: Company name for filename
            
        Returns:
            list[GeneratedDocument]: Generated document information
            
        TODO: Implement in Phase 4
        """
        logger.info(
            f"Generating documents",
            extra={
                "formats": formats,
                "job_title": job_title or "Unknown",
                "company": company or "Unknown",
                "content_length": len(content),
            },
        )
        
        # Validate formats
        invalid_formats = set(formats) - self.SUPPORTED_FORMATS
        if invalid_formats:
            logger.error(f"Invalid formats requested: {invalid_formats}")
            raise ValueError(f"Unsupported formats: {invalid_formats}")
        
        # Placeholder implementation
        logger.debug("Document generation not yet implemented (Phase 4)")
        return []
    
    def _generate_filename(
        self,
        format: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
    ) -> str:
        """
        Generate a descriptive filename for the output document.
        
        Args:
            format: File format (pdf/docx)
            job_title: Optional job title
            company: Optional company name
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        parts = ["resume", "tailored"]
        
        if company:
            # Sanitize company name for filename
            safe_company = "".join(c if c.isalnum() else "_" for c in company)
            parts.append(safe_company[:30])
        
        if job_title:
            # Sanitize job title for filename
            safe_title = "".join(c if c.isalnum() else "_" for c in job_title)
            parts.append(safe_title[:30])
        
        parts.append(timestamp)
        
        filename = f"{'_'.join(parts)}.{format}"
        logger.debug(f"Generated filename: {filename}")
        
        return filename
    
    def _generate_pdf(self, content: str, output_path: Path) -> None:
        """
        Generate a PDF document.
        
        TODO: Implement in Phase 4
        """
        logger.debug(f"PDF generation not yet implemented: {output_path}")
        raise NotImplementedError("PDF generation implemented in Phase 4")
    
    def _generate_docx(self, content: str, output_path: Path) -> None:
        """
        Generate a DOCX document.
        
        TODO: Implement in Phase 4
        """
        logger.debug(f"DOCX generation not yet implemented: {output_path}")
        raise NotImplementedError("DOCX generation implemented in Phase 4")
