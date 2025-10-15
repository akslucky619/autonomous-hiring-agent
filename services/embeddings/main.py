from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import numpy as np
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Embeddings Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/hiring_automation")

class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

class DatabaseEmbeddingRequest(BaseModel):
    text: str
    candidate_id: str = None
    jd_id: str = None

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

def pull_ollama_model():
    """Pull the embedding model from Ollama"""
    try:
        response = requests.post(f"{OLLAMA_URL}/api/pull", json={
            "name": "nomic-embed-text",
            "stream": False
        })
        if response.status_code == 200:
            print("Successfully pulled nomic-embed-text model")
        else:
            print(f"Failed to pull model: {response.text}")
    except Exception as e:
        print(f"Error pulling model: {e}")

def get_embedding(text: str) -> List[float]:
    """Get embedding from Ollama"""
    try:
        response = requests.post(f"{OLLAMA_URL}/api/embeddings", json={
            "model": "nomic-embed-text",
            "prompt": text
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data["embedding"]
        else:
            raise HTTPException(status_code=500, detail=f"Ollama API error: {response.text}")
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize the service"""
    print("Pulling embedding model...")
    pull_ollama_model()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/embed", response_model=EmbeddingResponse)
async def create_embedding(request: EmbeddingRequest):
    """Create embedding for given text"""
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        embedding = get_embedding(request.text)
        return EmbeddingResponse(embedding=embedding)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")

@app.post("/embed-and-store-candidate")
async def embed_and_store_candidate(request: DatabaseEmbeddingRequest):
    """Create embedding and store it in database for a candidate"""
    
    if not request.candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id is required")
    
    try:
        # Get embedding
        embedding = get_embedding(request.text)
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        cursor.execute(
            "UPDATE candidates SET embedding = %s WHERE id = %s",
            (embedding_str, request.candidate_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "candidate_id": request.candidate_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing embedding: {str(e)}")

@app.post("/embed-and-store-jd")
async def embed_and_store_jd(request: DatabaseEmbeddingRequest):
    """Create embedding and store it in database for a job description"""
    
    if not request.jd_id:
        raise HTTPException(status_code=400, detail="jd_id is required")
    
    try:
        # Get embedding
        embedding = get_embedding(request.text)
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        cursor.execute(
            "UPDATE job_descriptions SET embedding = %s WHERE id = %s",
            (embedding_str, request.jd_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "jd_id": request.jd_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing embedding: {str(e)}")

@app.get("/search-similar")
async def search_similar(text: str, limit: int = 10):
    """Find similar candidates based on text"""
    
    try:
        # Get embedding for search text
        embedding = get_embedding(text)
        
        # Search in database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Convert embedding to string format for PostgreSQL
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        cursor.execute("""
            SELECT 
                id,
                name,
                email,
                location,
                skills,
                total_years_experience,
                1 - (embedding <=> %s) as similarity_score
            FROM candidates 
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s
            LIMIT %s
        """, (embedding_str, embedding_str, limit))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return {"results": [dict(row) for row in results]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
