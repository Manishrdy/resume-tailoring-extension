"""
Gemini AI Service

Handles communication with Google's Gemini API for resume tailoring.
Provides prompt construction, API calls, response parsing, and error handling.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from logger import get_logger

# Module logger
logger = get_logger(__name__)


@dataclass
class JobDetails:
    """Extracted information from a job description."""
    
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None  # Full-time, Part-time, Contract
    experience_level: Optional[str] = None  # Entry, Mid, Senior
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    salary_range: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "employment_type": self.employment_type,
            "experience_level": self.experience_level,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "responsibilities": self.responsibilities,
            "requirements": self.requirements,
            "benefits": self.benefits,
            "salary_range": self.salary_range,
        }


@dataclass
class TailoredContent:
    """Result of AI-powered resume tailoring."""
    
    tailored_text: str
    summary: Optional[str] = None
    matched_keywords: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    ats_score: Optional[int] = None  # Estimated ATS compatibility (0-100)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "tailored_text": self.tailored_text,
            "summary": self.summary,
            "matched_keywords": self.matched_keywords,
            "suggestions": self.suggestions,
            "ats_score": self.ats_score,
        }


class GeminiService:
    """
    Service for interacting with Google Gemini API.
    
    Handles prompt construction, API calls, and response parsing
    for resume tailoring operations.
    
    Usage:
        from config import settings
        service = GeminiService(settings.gemini_api_key, settings.gemini_model)
        result = service.tailor_resume(resume_text, job_description)
    """
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Initialize the Gemini service.
        
        Args:
            api_key: Google Gemini API key (from config.settings.gemini_api_key)
            model: Model name to use (from config.settings.gemini_model)
        """
        self.api_key = api_key
        self.model = model
        self._client = None
        self._model_instance = None
        
        logger.info(f"Initializing GeminiService with model: {model}")
        
        if not api_key:
            logger.warning("Gemini API key not provided - service will not function")
        else:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Gemini client."""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            self._client = genai
            self._model_instance = genai.GenerativeModel(self.model)
            
            logger.info(f"Gemini client initialized successfully with model: {self.model}")
            
        except ImportError:
            logger.error("google-generativeai not installed. Run: pip install google-generativeai")
            raise ImportError(
                "google-generativeai is required. Install with: pip install google-generativeai"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise RuntimeError(f"Failed to initialize Gemini client: {e}")
    
    def _ensure_client(self) -> None:
        """Ensure the client is initialized."""
        if not self._model_instance:
            if not self.api_key:
                raise RuntimeError("Gemini API key not configured")
            self._initialize_client()
    
    def tailor_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: Optional[str] = None,
        company: Optional[str] = None,
        emphasis_keywords: Optional[list[str]] = None,
    ) -> TailoredContent:
        """
        Tailor the resume content based on job description.
        
        Args:
            resume_text: Original resume content
            job_description: Target job description
            job_title: Optional job title for context
            company: Optional company name for context
            emphasis_keywords: Additional keywords to emphasize
            
        Returns:
            TailoredContent: AI-tailored resume content
        """
        self._ensure_client()
        
        logger.info(
            f"Tailoring resume for: {job_title or 'Unknown Position'} at {company or 'Unknown Company'}"
        )
        logger.debug(f"Resume length: {len(resume_text)} chars, JD length: {len(job_description)} chars")
        
        # Build the prompt
        prompt = self._build_tailor_prompt(
            resume_text=resume_text,
            job_description=job_description,
            job_title=job_title,
            company=company,
            emphasis_keywords=emphasis_keywords,
        )
        
        try:
            # Call Gemini API
            logger.debug("Sending request to Gemini API...")
            response = self._model_instance.generate_content(prompt)
            
            # Parse response
            result = self._parse_tailor_response(response.text)
            
            logger.info(
                f"Resume tailored successfully. "
                f"Matched {len(result.matched_keywords)} keywords, "
                f"ATS score: {result.ats_score}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini API error during tailoring: {e}")
            raise RuntimeError(f"Failed to tailor resume: {e}")
    
    def extract_job_details(self, job_description: str) -> JobDetails:
        """
        Extract structured information from job description.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            JobDetails: Extracted job details
        """
        self._ensure_client()
        
        logger.info("Extracting job details from description")
        logger.debug(f"Job description length: {len(job_description)} chars")
        
        prompt = self._build_extraction_prompt(job_description)
        
        try:
            response = self._model_instance.generate_content(prompt)
            result = self._parse_extraction_response(response.text)
            
            logger.info(
                f"Job details extracted: {result.title or 'Unknown'} at {result.company or 'Unknown'}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract job details: {e}")
            # Return empty JobDetails rather than failing
            return JobDetails()
    
    def _build_tailor_prompt(
        self,
        resume_text: str,
        job_description: str,
        job_title: Optional[str],
        company: Optional[str],
        emphasis_keywords: Optional[list[str]],
    ) -> str:
        """
        Build the prompt for resume tailoring.
        
        Args:
            resume_text: Original resume content
            job_description: Target job description
            job_title: Optional job title
            company: Optional company name
            emphasis_keywords: Additional keywords to emphasize
            
        Returns:
            str: Formatted prompt for Gemini
        """
        keywords_section = ""
        if emphasis_keywords:
            keywords_section = f"\n\nAdditional keywords to emphasize: {', '.join(emphasis_keywords)}"
        
        context_section = ""
        if job_title or company:
            parts = []
            if job_title:
                parts.append(f"Position: {job_title}")
            if company:
                parts.append(f"Company: {company}")
            context_section = f"\n\nTarget Position Information:\n{chr(10).join(parts)}"
        
        prompt = f"""You are an expert resume writer and career coach. Your task is to tailor the given resume to better match the job description while maintaining authenticity and truthfulness.

IMPORTANT RULES:
1. DO NOT fabricate or add skills/experiences the candidate doesn't have
2. Reorder and emphasize existing relevant experiences
3. Use keywords from the job description naturally where applicable
4. Improve phrasing to highlight relevant achievements
5. Keep the same overall structure but optimize content
6. Make it ATS (Applicant Tracking System) friendly
7. Quantify achievements where possible based on existing information

{context_section}
{keywords_section}

===== ORIGINAL RESUME =====
{resume_text}
===== END RESUME =====

===== JOB DESCRIPTION =====
{job_description}
===== END JOB DESCRIPTION =====

Please provide your response in the following format:

<TAILORED_RESUME>
[The complete tailored resume text here, formatted professionally]
</TAILORED_RESUME>

<SUMMARY>
[A brief 2-3 sentence summary of the main changes made]
</SUMMARY>

<MATCHED_KEYWORDS>
[Comma-separated list of keywords from the job description that match the candidate's experience]
</MATCHED_KEYWORDS>

<SUGGESTIONS>
[Bullet points with 3-5 additional suggestions for the candidate to strengthen their application]
</SUGGESTIONS>

<ATS_SCORE>
[A number from 0-100 estimating how well this resume will perform with ATS systems for this specific job]
</ATS_SCORE>

Now tailor the resume:"""
        
        return prompt
    
    def _build_extraction_prompt(self, job_description: str) -> str:
        """
        Build prompt for extracting job details.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            str: Formatted prompt for Gemini
        """
        prompt = f"""Analyze the following job description and extract key information. 
Return your response in JSON format.

===== JOB DESCRIPTION =====
{job_description}
===== END JOB DESCRIPTION =====

Extract and return a JSON object with these fields:
{{
    "title": "Job title",
    "company": "Company name (if mentioned)",
    "location": "Location (if mentioned)",
    "employment_type": "Full-time/Part-time/Contract/etc",
    "experience_level": "Entry/Mid/Senior/Lead/etc",
    "required_skills": ["list", "of", "required", "skills"],
    "preferred_skills": ["list", "of", "preferred/nice-to-have", "skills"],
    "responsibilities": ["key", "job", "responsibilities"],
    "requirements": ["education", "experience", "other requirements"],
    "benefits": ["listed", "benefits"],
    "salary_range": "Salary range if mentioned"
}}

Return ONLY the JSON object, no additional text.
JSON Response:"""
        
        return prompt
    
    def _parse_tailor_response(self, response_text: str) -> TailoredContent:
        """
        Parse the tailoring response from Gemini.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            TailoredContent: Parsed tailored content
        """
        logger.debug("Parsing tailor response")
        
        # Extract sections using regex
        tailored_resume = ""
        summary = None
        matched_keywords = []
        suggestions = []
        ats_score = None
        
        # Extract tailored resume
        resume_match = re.search(
            r"<TAILORED_RESUME>\s*(.*?)\s*</TAILORED_RESUME>",
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if resume_match:
            tailored_resume = resume_match.group(1).strip()
        else:
            # If no tags, try to extract the main content
            logger.warning("Could not find TAILORED_RESUME tags, using full response")
            tailored_resume = response_text
        
        # Extract summary
        summary_match = re.search(
            r"<SUMMARY>\s*(.*?)\s*</SUMMARY>",
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if summary_match:
            summary = summary_match.group(1).strip()
        
        # Extract matched keywords
        keywords_match = re.search(
            r"<MATCHED_KEYWORDS>\s*(.*?)\s*</MATCHED_KEYWORDS>",
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            matched_keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
        
        # Extract suggestions
        suggestions_match = re.search(
            r"<SUGGESTIONS>\s*(.*?)\s*</SUGGESTIONS>",
            response_text,
            re.DOTALL | re.IGNORECASE
        )
        if suggestions_match:
            suggestions_text = suggestions_match.group(1).strip()
            # Parse bullet points
            suggestions = [
                line.strip().lstrip("•-*").strip()
                for line in suggestions_text.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
        
        # Extract ATS score
        ats_match = re.search(
            r"<ATS_SCORE>\s*(\d+)\s*</ATS_SCORE>",
            response_text,
            re.IGNORECASE
        )
        if ats_match:
            try:
                ats_score = int(ats_match.group(1))
                ats_score = max(0, min(100, ats_score))  # Clamp to 0-100
            except ValueError:
                pass
        
        return TailoredContent(
            tailored_text=tailored_resume,
            summary=summary,
            matched_keywords=matched_keywords,
            suggestions=suggestions,
            ats_score=ats_score,
        )
    
    def _parse_extraction_response(self, response_text: str) -> JobDetails:
        """
        Parse the job extraction response from Gemini.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            JobDetails: Parsed job details
        """
        logger.debug("Parsing extraction response")
        
        # Try to extract JSON from the response
        try:
            # Clean up the response - remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"```json?\s*", "", cleaned)
                cleaned = re.sub(r"```\s*$", "", cleaned)
            
            # Parse JSON
            data = json.loads(cleaned)
            
            return JobDetails(
                title=data.get("title"),
                company=data.get("company"),
                location=data.get("location"),
                employment_type=data.get("employment_type"),
                experience_level=data.get("experience_level"),
                required_skills=data.get("required_skills", []),
                preferred_skills=data.get("preferred_skills", []),
                responsibilities=data.get("responsibilities", []),
                requirements=data.get("requirements", []),
                benefits=data.get("benefits", []),
                salary_range=data.get("salary_range"),
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            
            # Try to extract basic info using regex
            title_match = re.search(r'"title"\s*:\s*"([^"]+)"', response_text)
            company_match = re.search(r'"company"\s*:\s*"([^"]+)"', response_text)
            
            return JobDetails(
                title=title_match.group(1) if title_match else None,
                company=company_match.group(1) if company_match else None,
            )
    
    def test_connection(self) -> bool:
        """
        Test the connection to Gemini API.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self._ensure_client()
            
            response = self._model_instance.generate_content("Say 'Connection successful' in exactly those words.")
            
            if response and response.text:
                logger.info("Gemini API connection test successful")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {e}")
            return False
