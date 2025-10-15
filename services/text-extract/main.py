from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io
import re
from typing import Dict, List, Any
import spacy
from pydantic import BaseModel

app = FastAPI(title="Text Extraction Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load spaCy model for NER (model is installed via requirements)
nlp = spacy.load("en_core_web_sm")

class ExtractionResult(BaseModel):
    text: str
    skills: List[str]
    experience_years: float
    location: str
    email: str
    name: str
    structured_data: Dict[str, Any]

# Skill normalization mapping
SKILL_MAP = {
    "python": ["python", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "react": ["react", "reactjs", "react.js"],
    "node": ["node", "nodejs", "node.js"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker", "dockerfile"],
    "postgresql": ["postgresql", "postgres", "pg"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "sql": ["sql", "mysql", "sqlite"],
    "git": ["git", "github", "gitlab"],
    "linux": ["linux", "unix"],
    "kubernetes": ["kubernetes", "k8s"],
    "redis": ["redis"],
    "mongodb": ["mongodb", "mongo"],
    "graphql": ["graphql", "graph ql"],
    "machine learning": ["machine learning", "ml", "deep learning", "ai"],
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
}

def normalize_skills(text: str) -> List[str]:
    """Extract and normalize skills from text"""
    text_lower = text.lower()
    found_skills = set()
    
    for skill, variations in SKILL_MAP.items():
        for variation in variations:
            if variation in text_lower:
                found_skills.add(skill)
                break
    
    return list(found_skills)

def extract_experience(text: str) -> float:
    """Extract years of experience from text"""
    # Look for patterns like "5 years", "3+ years", etc.
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'(\d+)\+?\s*years?\s*in\s*\w+',
        r'experience:\s*(\d+)\+?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            return float(matches[0])
    
    return 0.0

def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract email and name from text"""
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Extract name (simple heuristic - first line that looks like a name)
    lines = text.split('\n')[:10]  # Check first 10 lines
    name = ""
    for line in lines:
        line = line.strip()
        if len(line) > 2 and len(line) < 50 and not any(word in line.lower() for word in ['resume', 'cv', 'experience', 'education']):
            if len(line.split()) >= 2:  # Has at least first and last name
                name = line
                break
    
    return {
        "email": emails[0] if emails else "",
        "name": name
    }

def extract_location(text: str) -> str:
    """Extract location from text"""
    doc = nlp(text[:1000])  # Process first 1000 chars for speed
    
    for ent in doc.ents:
        if ent.label_ == "GPE":  # Geopolitical entity
            return ent.text
    
    # Fallback: look for common location patterns
    location_patterns = [
        r'([A-Z][a-z]+,\s*[A-Z]{2})',  # City, State
        r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    
    return ""

def extract_pdf_text(file_content: bytes) -> str:
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting PDF text: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/extract", response_model=ExtractionResult)
async def extract_text(file: UploadFile = File(...)):
    """Extract text and structured data from uploaded file"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read file content
    content = await file.read()
    
    # Extract text based on file type
    if file.filename.lower().endswith('.pdf'):
        text = extract_pdf_text(content)
    elif file.filename.lower().endswith(('.txt', '.md')):
        text = content.decode('utf-8')
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and TXT files are supported.")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found in file")
    
    # Extract structured information
    skills = normalize_skills(text)
    experience_years = extract_experience(text)
    location = extract_location(text)
    contact_info = extract_contact_info(text)
    
    # Create structured data
    structured_data = {
        "skills": skills,
        "experience_years": experience_years,
        "location": location,
        "email": contact_info["email"],
        "name": contact_info["name"],
        "file_name": file.filename,
        "text_length": len(text)
    }
    
    return ExtractionResult(
        text=text,
        skills=skills,
        experience_years=experience_years,
        location=location,
        email=contact_info["email"],
        name=contact_info["name"],
        structured_data=structured_data
    )

@app.post("/extract-job-description", response_model=ExtractionResult)
async def extract_job_description(jd_text: str):
    """Extract structured data from job description text"""
    
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Extract structured information
    skills = normalize_skills(jd_text)
    experience_years = extract_experience(jd_text)
    location = extract_location(jd_text)
    
    # For job descriptions, we don't extract email/name
    structured_data = {
        "skills": skills,
        "experience_years": experience_years,
        "location": location,
        "text_length": len(jd_text)
    }
    
    return ExtractionResult(
        text=jd_text,
        skills=skills,
        experience_years=experience_years,
        location=location,
        email="",
        name="",
        structured_data=structured_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
