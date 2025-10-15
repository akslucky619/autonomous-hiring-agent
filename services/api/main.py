from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime

app = FastAPI(title="Hiring Automation API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/hiring_automation")
TEXT_EXTRACT_URL = os.getenv("TEXT_EXTRACT_URL", "http://text-extract:8001")
EMBEDDINGS_URL = os.getenv("EMBEDDINGS_URL", "http://embeddings:8002")

# Pydantic models
class CandidateCreate(BaseModel):
    name: str
    email: str
    location: str
    work_authorization: str
    total_years_experience: float
    skills: List[str]
    raw_text: str

class JobDescriptionCreate(BaseModel):
    title: str
    location: str
    required_skills: List[str]
    optional_skills: List[str]
    min_years_experience: float
    raw_text: str

class RankingRequest(BaseModel):
    jd_id: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50

class RankingResult(BaseModel):
    candidate_id: str
    name: str
    email: str
    location: str
    skills: List[str]
    total_years_experience: float
    similarity_score: float
    skill_overlap_score: float
    experience_score: float
    final_score: float
    explanation: Dict[str, Any]

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/candidates")
async def get_candidates():
    """Get all candidates"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, name, email, location, work_authorization, 
                   total_years_experience, skills, created_at
            FROM candidates 
            ORDER BY created_at DESC
        """)
        
        candidates = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"candidates": [dict(candidate) for candidate in candidates]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")

@app.get("/job-descriptions")
async def get_job_descriptions():
    """Get all job descriptions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, title, location, required_skills, optional_skills,
                   min_years_experience, created_at
            FROM job_descriptions 
            ORDER BY created_at DESC
        """)
        
        jds = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"job_descriptions": [dict(jd) for jd in jds]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job descriptions: {str(e)}")

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process a resume"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        # Extract text using text-extract service
        extract_response = requests.post(
            f"{TEXT_EXTRACT_URL}/extract",
            files={"file": (file.filename, await file.read(), file.content_type)}
        )
        
        if extract_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Error extracting text from file")
        
        extract_data = extract_response.json()
        
        # Create candidate record
        candidate_data = CandidateCreate(
            name=extract_data["name"],
            email=extract_data["email"],
            location=extract_data["location"],
            work_authorization="Unknown",  # Default value
            total_years_experience=extract_data["experience_years"],
            skills=extract_data["skills"],
            raw_text=extract_data["text"]
        )
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        candidate_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO candidates (id, name, email, location, work_authorization,
                                  total_years_experience, skills, raw_text, structured_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            candidate_id,
            candidate_data.name,
            candidate_data.email,
            candidate_data.location,
            candidate_data.work_authorization,
            candidate_data.total_years_experience,
            candidate_data.skills,
            candidate_data.raw_text,
            json.dumps(extract_data["structured_data"])
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Generate embedding
        embedding_response = requests.post(
            f"{EMBEDDINGS_URL}/embed-and-store-candidate",
            json={
                "text": candidate_data.raw_text,
                "candidate_id": candidate_id
            }
        )
        
        if embedding_response.status_code != 200:
            print(f"Warning: Failed to generate embedding for candidate {candidate_id}")
        
        return {
            "status": "success",
            "candidate_id": candidate_id,
            "extracted_data": extract_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/create-job-description")
async def create_job_description(jd_data: JobDescriptionCreate):
    """Create a new job description"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        jd_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO job_descriptions (id, title, location, required_skills, optional_skills,
                                        min_years_experience, raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            jd_id,
            jd_data.title,
            jd_data.location,
            jd_data.required_skills,
            jd_data.optional_skills,
            jd_data.min_years_experience,
            jd_data.raw_text
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Generate embedding
        embedding_response = requests.post(
            f"{EMBEDDINGS_URL}/embed-and-store-jd",
            json={
                "text": jd_data.raw_text,
                "jd_id": jd_id
            }
        )
        
        if embedding_response.status_code != 200:
            print(f"Warning: Failed to generate embedding for JD {jd_id}")
        
        return {
            "status": "success",
            "jd_id": jd_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job description: {str(e)}")

@app.post("/rank-candidates")
async def rank_candidates(request: RankingRequest):
    """Rank candidates for a job description"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get job description
        cursor.execute("SELECT * FROM job_descriptions WHERE id = %s", (request.jd_id,))
        jd = cursor.fetchone()
        
        if not jd:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        # Get candidates with embeddings
        cursor.execute("""
            SELECT 
                c.id, c.name, c.email, c.location, c.skills, c.total_years_experience,
                c.work_authorization, c.raw_text,
                1 - (c.embedding <=> jd.embedding) as similarity_score
            FROM candidates c
            CROSS JOIN job_descriptions jd
            WHERE jd.id = %s AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> jd.embedding
            LIMIT 200
        """, (request.jd_id,))
        
        candidates = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Apply filters and calculate scores
        results = []
        for candidate in candidates:
            # Apply hard filters
            if request.filters:
                if "location" in request.filters and request.filters["location"]:
                    if request.filters["location"].lower() not in candidate["location"].lower():
                        continue
                
                if "min_experience" in request.filters:
                    if candidate["total_years_experience"] < request.filters["min_experience"]:
                        continue
                
                if "work_auth" in request.filters and request.filters["work_auth"]:
                    if candidate["work_authorization"].lower() != request.filters["work_auth"].lower():
                        continue
            
            # Calculate skill overlap score
            jd_skills = set(jd["required_skills"] + jd["optional_skills"])
            candidate_skills = set(candidate["skills"])
            skill_overlap_score = len(jd_skills & candidate_skills) / len(jd_skills) if jd_skills else 0
            
            # Calculate experience score
            experience_score = min(candidate["total_years_experience"] / jd["min_years_experience"], 1.0) if jd["min_years_experience"] > 0 else 1.0
            
            # Calculate final score (weighted combination)
            final_score = (
                0.40 * candidate["similarity_score"] +
                0.35 * skill_overlap_score +
                0.25 * experience_score
            )
            
            # Create explanation
            explanation = {
                "matched_skills": list(jd_skills & candidate_skills),
                "missing_skills": list(jd_skills - candidate_skills),
                "experience_ratio": candidate["total_years_experience"] / jd["min_years_experience"] if jd["min_years_experience"] > 0 else 1.0,
                "similarity_breakdown": {
                    "semantic_similarity": candidate["similarity_score"],
                    "skill_overlap": skill_overlap_score,
                    "experience_match": experience_score
                }
            }
            
            results.append(RankingResult(
                candidate_id=candidate["id"],
                name=candidate["name"],
                email=candidate["email"],
                location=candidate["location"],
                skills=candidate["skills"],
                total_years_experience=candidate["total_years_experience"],
                similarity_score=candidate["similarity_score"],
                skill_overlap_score=skill_overlap_score,
                experience_score=experience_score,
                final_score=final_score,
                explanation=explanation
            ))
        
        # Sort by final score and return top results
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        return {
            "job_description": dict(jd),
            "results": results[:request.limit],
            "total_candidates": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ranking candidates: {str(e)}")

@app.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: str):
    """Get candidate details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        return {"candidate": dict(candidate)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}")

@app.get("/job-description/{jd_id}")
async def get_job_description(jd_id: str):
    """Get job description details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM job_descriptions WHERE id = %s", (jd_id,))
        jd = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not jd:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        return {"job_description": dict(jd)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job description: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
