# Resume Tailor

AI-powered Chrome extension that tailors your resume to match job descriptions using Google's Gemini API.

## Overview

Resume Tailor is a local-first tool that:
1. Captures job descriptions from any webpage via Chrome extension
2. Analyzes the job requirements using Gemini AI
3. Tailors your resume to highlight relevant skills and experience
4. Generates professionally formatted PDF and DOCX outputs

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│  Chrome Extension   │  HTTP   │  Local Python Server │
│  (JavaScript)       │◄───────►│  (FastAPI)          │
│                     │ :5000   │                      │
│  • Capture webpage  │         │  • Parse resume      │
│  • UI/Popup         │         │  • Call Gemini API   │
│  • Download file    │         │  • Generate PDF/DOCX │
└─────────────────────┘         └─────────────────────┘
```

## Key Design Principles

### 1. Centralized Logging
All logging goes through `/backend/logger.py`. Never create loggers directly:

```python
# Correct
from logger import get_logger
logger = get_logger(__name__)

# Wrong - Don't do this
import logging
logger = logging.getLogger(__name__)
```

### 2. Configuration via .env Only
All file paths (especially resume) are accessed ONLY through configuration:

```python
# Correct - Always use config
from config import settings
resume_path = settings.resume_path

# Wrong - Never hardcode paths
resume_path = Path("resume/my_resume.pdf")
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Chrome or Chromium browser
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### 1. Setup Backend

```bash
# Navigate to project directory
cd resume-tailor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` and configure:

```env
# REQUIRED: Your Gemini API key
GEMINI_API_KEY=your_actual_api_key

# REQUIRED: Your resume filename
RESUME_FILENAME=your_resume.pdf
```

### 3. Add Your Resume

Place your resume in the `resume/` directory:
```bash
cp /path/to/your/resume.pdf resume/
```

Then update `RESUME_FILENAME` in `.env` to match.

### 4. Start the Server

```bash
cd backend
python app.py
```

Or with uvicorn:
```bash
uvicorn app:app --host 127.0.0.1 --port 5000 --reload
```

### 5. Verify Installation

- **Swagger Docs:** http://localhost:5000/docs
- **Health Check:** http://localhost:5000/health
- **Configuration:** http://localhost:5000/config

## Project Structure

```
resume-tailor/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── config.py              # Centralized configuration
│   ├── logger.py              # Centralized logging service
│   ├── models.py              # Pydantic models
│   ├── exceptions.py          # Custom exceptions
│   ├── services/
│   │   ├── resume_parser.py   # Resume parsing (PDF/DOCX)
│   │   ├── gemini_service.py  # Gemini AI integration
│   │   └── document_gen.py    # PDF/DOCX generation
│   ├── outputs/               # Generated resumes
│   ├── logs/                  # Application logs
│   └── requirements.txt
│
├── extension/                 # Chrome extension (Phase 5-6)
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   └── content.js
│
├── resume/                    # Your base resume(s)
│   └── (your resume here)
│
├── .env                       # Environment configuration
├── .env.example               # Example configuration
├── .gitignore
└── README.md
```

## Configuration Reference

All configuration is done via `.env` file:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key | - |
| `RESUME_FILENAME` | Yes | Resume filename in /resume | - |
| `RESUME_DIR_NAME` | No | Resume directory name | `resume` |
| `GEMINI_MODEL` | No | Gemini model to use | `gemini-1.5-flash` |
| `HOST` | No | Server host | `127.0.0.1` |
| `PORT` | No | Server port | `5000` |
| `DEBUG` | No | Enable debug mode | `false` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `LOG_JSON` | No | JSON formatted logs | `false` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check and dependency status |
| GET | `/config` | Current configuration (non-sensitive) |
| GET | `/resume/info` | Resume file information |
| POST | `/tailor` | Tailor resume to job description |
| GET | `/docs` | Interactive API documentation |

## Logging

Logs are written to:
- **Console:** Colored output for development
- **app.log:** All application logs (rotating, 10MB max)
- **error.log:** Error-level logs only
- **app.json.log:** JSON formatted logs (when `LOG_JSON=true`)

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging information |
| INFO | General operational messages |
| WARNING | Warning messages |
| ERROR | Error messages |
| CRITICAL | Critical errors |

## Development

### Running Tests

```bash
pytest backend/tests/ -v
```

### Type Checking

```bash
mypy backend/
```

### Code Formatting

```bash
pip install black isort
black backend/
isort backend/
```

## Troubleshooting

### "RESUME_FILENAME must be set in .env"

Ensure your `.env` file contains:
```env
RESUME_FILENAME=your_resume.pdf
```

### "Resume file not found"

1. Check that your resume file exists in the `resume/` directory
2. Verify `RESUME_FILENAME` in `.env` matches exactly (case-sensitive)
3. Ensure file format is supported (.pdf or .docx)

### Server won't start

1. Check logs in `backend/logs/app.log`
2. Verify `.env` file exists and is properly configured
3. Ensure all dependencies are installed

### CORS errors

The server accepts requests from Chrome extensions. For other origins, modify `allow_origins` in `app.py`.

## Roadmap

- [x] Phase 1: Backend foundation with centralized logging
- [ ] Phase 2: Resume parser
- [ ] Phase 3: Gemini AI integration
- [ ] Phase 4: Document generation
- [ ] Phase 5: Chrome extension (basic)
- [ ] Phase 6: Content extraction
- [ ] Phase 7: Full integration

## License

MIT License - feel free to use and modify for your needs.
