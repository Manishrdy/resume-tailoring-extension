"""
Resume Parser Service

Handles reading and parsing resume files (PDF and DOCX formats).
Full implementation in Phase 2.

IMPORTANT: Resume path must be passed in, obtained from config.settings.resume_path
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from logger import get_logger

# Module logger
logger = get_logger(__name__)


@dataclass
class ParsedResume:
    """Structured representation of a parsed resume."""
    
    raw_text: str
    filename: str
    format: str
    sections: Optional[dict[str, str]] = None
    contact_info: Optional[dict[str, str]] = None
    skills: Optional[list[str]] = None


class ResumeParser:
    """
    Service for parsing resume files.
    
    Supports PDF and DOCX formats.
    
    Usage:
        from config import settings
        parser = ResumeParser(settings.resume_path)
        resume = parser.parse()
    """
    
    SUPPORTED_FORMATS = {".pdf", ".docx", ".doc"}
    
    def __init__(self, resume_path: Path):
        """
        Initialize the parser with a resume file path.
        
        Args:
            resume_path: Path to the resume file (from config.settings.resume_path)
        """
        self.resume_path = resume_path
        logger.debug(f"Initializing ResumeParser for: {resume_path}")
        self._validate_file()
    
    def _validate_file(self) -> None:
        """Validate that the resume file exists and is supported."""
        logger.debug(f"Validating resume file: {self.resume_path}")
        
        if not self.resume_path.exists():
            logger.error(f"Resume file not found: {self.resume_path}")
            raise FileNotFoundError(f"Resume file not found: {self.resume_path}")
        
        if self.resume_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            logger.error(f"Unsupported resume format: {self.resume_path.suffix}")
            raise ValueError(
                f"Unsupported format: {self.resume_path.suffix}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )
        
        logger.info(f"Resume file validated: {self.resume_path.name}")
    
    def parse(self) -> ParsedResume:
        """
        Parse the resume file and extract content.
        
        Returns:
            ParsedResume: Structured resume data
            
        TODO: Implement in Phase 2
        """
        logger.info(f"Parsing resume: {self.resume_path.name}")
        
        # Placeholder implementation
        result = ParsedResume(
            raw_text="[Resume content will be extracted in Phase 2]",
            filename=self.resume_path.name,
            format=self.resume_path.suffix.lower(),
        )
        
        logger.debug(f"Resume parsed (placeholder): {result.filename}")
        return result
    
    def _parse_pdf(self) -> str:
        """Extract text from PDF file. Implemented in Phase 2."""
        logger.debug("PDF parsing not yet implemented")
        raise NotImplementedError("PDF parsing implemented in Phase 2")
    
    def _parse_docx(self) -> str:
        """Extract text from DOCX file. Implemented in Phase 2."""
        logger.debug("DOCX parsing not yet implemented")
        raise NotImplementedError("DOCX parsing implemented in Phase 2")
