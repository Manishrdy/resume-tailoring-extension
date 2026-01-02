# Resume Tailor

AI-powered Chrome extension that automatically tailors your resume to match job descriptions using Google's Gemini API.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-gray)

## Features

- 🤖 **AI-Powered Tailoring** - Uses Google Gemini to intelligently rewrite your resume
- 📄 **Multi-Format Support** - Reads PDF/DOCX resumes, outputs PDF/DOCX
- 🔍 **Smart Extraction** - Automatically extracts job descriptions from job sites
- 📊 **ATS Scoring** - Estimates how well your resume will perform with ATS systems
- 🏷️ **Keyword Matching** - Shows which keywords from the job description match your experience
- 💡 **Suggestions** - Provides actionable recommendations to improve your resume
- 🔒 **Local Processing** - All data stays on your machine

## Architecture

```
┌─────────────────────────┐              ┌─────────────────────────┐
│   Chrome Extension      │    HTTP      │    Python Backend       │
│   ─────────────────     │◄────────────►│    ───────────────      │
│                         │  localhost   │                         │
│   • Extract JD from     │    :5000     │   • Parse Resume        │
│     job pages           │              │   • Gemini AI           │
│   • Beautiful UI        │              │   • Generate PDF/DOCX   │
│   • Download files      │              │   • Logging & Config    │
└─────────────────────────┘              └─────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Chrome or Chromium browser
- Google Gemini API key ([Get one free](https://aistudio.google.com/app/apikey))

### 1. Setup Backend

```bash
# Clone or extract the project
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
# Copy example config
cp .env.example .env

# Edit .env with your settings
```

**Required settings in `.env`:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
RESUME_FILENAME=your_resume.pdf
```

### 3. Add Your Resume

```bash
# Copy your resume to the resume folder
cp /path/to/your/resume.pdf resume/

# Make sure RESUME_FILENAME in .env matches your file
```

### 4. Start the Server

```bash
cd backend
python app.py
```

Server will start at `http://localhost:5000`

### 5. Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select the `extension` folder from this project
5. Pin the extension to your toolbar

### 6. Generate Extension Icons (Optional)

```bash
cd extension/icons
pip install Pillow
python generate_icons.py
```

Then reload the extension in Chrome.

## Usage

### Using the Extension

1. Navigate to any job posting (LinkedIn, Indeed, Glassdoor, etc.)
2. Click the Resume Tailor extension icon
3. Click **Extract** to auto-fill the job description, or paste manually
4. (Optional) Add job title, company, and extra keywords
5. Select output formats (PDF, DOCX, or both)
6. Click **Tailor Resume**
7. Download your tailored resume files

### Using the API Directly

```bash
# Health check
curl http://localhost:5000/health

# Parse your resume
curl http://localhost:5000/resume/parse

# Tailor resume
curl -X POST http://localhost:5000/tailor \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a Senior Software Engineer...",
    "job_title": "Senior Software Engineer",
    "company": "TechCorp",
    "output_formats": ["pdf", "docx"]
  }'

# Download generated file
curl -O http://localhost:5000/download/resume_tailored_TechCorp_20240115_143022.pdf
```

## Project Structure

```
resume-tailor/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── config.py              # Configuration management
│   ├── logger.py              # Centralized logging
│   ├── models.py              # Pydantic models
│   ├── exceptions.py          # Custom exceptions
│   ├── services/
│   │   ├── resume_parser.py   # PDF/DOCX parsing
│   │   ├── gemini_service.py  # Gemini AI integration
│   │   └── document_gen.py    # PDF/DOCX generation
│   ├── outputs/               # Generated resumes
│   ├── logs/                  # Application logs
│   └── requirements.txt
│
├── extension/
│   ├── manifest.json          # Extension config
│   ├── popup.html             # Extension UI
│   ├── popup.css              # Extension styles
│   ├── popup.js               # Extension logic
│   ├── content.js             # Page content extraction
│   ├── background.js          # Service worker
│   └── icons/                 # Extension icons
│
├── resume/                    # Your base resume
├── .env                       # Configuration
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/config` | Current configuration |
| GET | `/resume/info` | Resume file info |
| GET | `/resume/parse` | Parse and analyze resume |
| POST | `/tailor` | Tailor resume to job |
| POST | `/job/extract` | Extract job details |
| GET | `/gemini/test` | Test Gemini connection |
| GET | `/download/{filename}` | Download generated file |
| GET | `/files` | List generated files |
| DELETE | `/files/cleanup` | Remove old files |
| GET | `/docs` | API documentation |

## Configuration

All configuration via `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Your Gemini API key |
| `RESUME_FILENAME` | Yes | - | Your resume filename |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model |
| `HOST` | No | `127.0.0.1` | Server host |
| `PORT` | No | `5000` | Server port |
| `DEBUG` | No | `false` | Debug mode |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `LOG_JSON` | No | `false` | JSON logging |

## Supported Job Sites

The extension automatically extracts job descriptions from:

- ✅ LinkedIn Jobs
- ✅ Indeed
- ✅ Glassdoor
- ✅ ZipRecruiter
- ✅ Lever.co
- ✅ Greenhouse.io
- ✅ Workday
- ✅ SmartRecruiters
- ✅ Most company career pages

For unsupported sites, simply copy and paste the job description.

## Troubleshooting

### Server won't start

1. Check `.env` file exists and has valid `GEMINI_API_KEY`
2. Verify resume file exists in `resume/` directory
3. Check logs: `backend/logs/app.log`

### Extension shows "Server not running"

1. Make sure backend is running: `python app.py`
2. Check if server is on correct port (default: 5000)
3. Try refreshing the extension

### "Resume file not found"

1. Place your resume in the `resume/` directory
2. Update `RESUME_FILENAME` in `.env` to match exactly

### Extraction not working

1. Some sites have anti-scraping measures
2. Try selecting text and right-click → "Tailor Resume with Selected Text"
3. Or manually copy/paste the job description

### PDF generation fails

Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0

# macOS
brew install pango

# Windows - usually works out of the box
```

## Development

### Running in Development Mode

```bash
# Backend with auto-reload
cd backend
DEBUG=true python app.py

# Or with uvicorn directly
uvicorn app:app --reload --host 127.0.0.1 --port 5000
```

### Running Tests

```bash
pip install pytest pytest-asyncio pytest-cov
pytest backend/tests/ -v --cov=backend
```

### Code Quality

```bash
pip install black isort mypy
black backend/
isort backend/
mypy backend/
```

## Tech Stack

**Backend:**
- FastAPI - Web framework
- Pydantic - Data validation
- Google Generative AI - Gemini integration
- PyMuPDF - PDF parsing
- python-docx - DOCX parsing/generation
- FPDF2 - PDF generation

**Extension:**
- Manifest V3 - Chrome extension
- Vanilla JavaScript - No framework dependencies
- Chrome APIs - Storage, scripting, tabs

## Roadmap

- [x] Phase 1: Backend foundation with centralized logging
- [x] Phase 2: Resume parser (PDF & DOCX support)
- [x] Phase 3: Gemini AI integration
- [x] Phase 4: Document generation (PDF/DOCX output)
- [x] Phase 5: Chrome extension (basic)
- [x] Phase 6: Content extraction from job sites
- [x] Phase 7: Full integration
- [ ] Future: Multiple resume profiles
- [ ] Future: Resume history/versioning
- [ ] Future: Cover letter generation
- [ ] Future: Interview prep suggestions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use and modify for your needs.

## Disclaimer

This tool is designed to help optimize your resume presentation. Always review the tailored output before submitting applications. The AI suggestions are meant to highlight your existing experience, not fabricate qualifications.
