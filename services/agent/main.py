from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime, timedelta
import asyncio
import schedule
import time
from threading import Thread
import logging

app = FastAPI(title="AI Hiring Agent", version="1.0.0")

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
API_URL = os.getenv("API_URL", "http://api:8000")
TEXT_EXTRACT_URL = os.getenv("TEXT_EXTRACT_URL", "http://text-extract:8001")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class AgentGoal(BaseModel):
    id: str
    title: str
    description: str
    target_positions: int
    deadline: datetime
    priority: str  # high, medium, low
    status: str  # active, completed, paused
    created_at: datetime

class AgentAction(BaseModel):
    id: str
    goal_id: str
    action_type: str  # search_candidates, send_outreach, schedule_interview, etc.
    status: str  # pending, completed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: datetime

class CandidateFeedback(BaseModel):
    candidate_id: str
    feedback_type: str  # hired, rejected, interview_scheduled, etc.
    feedback_score: float  # 0-1
    notes: str
    created_at: datetime

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

class AIHiringAgent:
    """Autonomous AI Hiring Agent"""
    
    def __init__(self):
        self.agent_id = str(uuid.uuid4())
        self.active_goals = []
        self.learning_data = {}
        self.last_action_time = datetime.now()
        
    async def create_goal(self, goal_data: dict) -> str:
        """Create a new hiring goal for the agent"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            goal_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO agent_goals (id, title, description, target_positions, 
                                       deadline, priority, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                goal_id,
                goal_data["title"],
                goal_data["description"],
                goal_data["target_positions"],
                goal_data["deadline"],
                goal_data["priority"],
                "active",
                datetime.now()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Start autonomous actions for this goal
            asyncio.create_task(self.execute_goal_strategy(goal_id))
            
            return goal_id
            
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            raise
    
    async def execute_goal_strategy(self, goal_id: str):
        """Execute autonomous strategy for a hiring goal"""
        try:
            # Get goal details
            goal = await self.get_goal(goal_id)
            if not goal:
                return
            
            logger.info(f"Starting autonomous strategy for goal: {goal['title']}")
            
            # Step 1: Analyze requirements and create search strategy
            search_strategy = await self.analyze_requirements(goal)
            
            # Step 2: Search for candidates (autonomous)
            candidates_found = await self.search_candidates_autonomously(search_strategy)
            
            # Step 3: Rank and filter candidates
            top_candidates = await self.rank_candidates_autonomously(goal_id, candidates_found)
            
            # Step 4: Send automated outreach
            await self.send_autonomous_outreach(goal_id, top_candidates)
            
            # Step 5: Schedule follow-ups
            await self.schedule_follow_ups(goal_id)
            
        except Exception as e:
            logger.error(f"Error executing goal strategy: {e}")
    
    async def analyze_requirements(self, goal: dict) -> dict:
        """Analyze job requirements and create search strategy"""
        try:
            # Get job descriptions for this goal
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM job_descriptions 
                WHERE title ILIKE %s OR raw_text ILIKE %s
                ORDER BY created_at DESC
            """, (f"%{goal['title']}%", f"%{goal['description']}%"))
            
            jds = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not jds:
                # Create a search strategy based on goal description
                return {
                    "search_keywords": self.extract_keywords(goal['description']),
                    "required_skills": self.extract_skills(goal['description']),
                    "experience_level": self.infer_experience_level(goal['description']),
                    "location_preferences": self.extract_location_preferences(goal['description'])
                }
            
            # Use existing JD data
            jd = jds[0]
            return {
                "jd_id": jd["id"],
                "required_skills": jd["required_skills"],
                "optional_skills": jd["optional_skills"],
                "min_experience": jd["min_years_experience"],
                "location": jd["location"]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing requirements: {e}")
            return {}
    
    async def search_candidates_autonomously(self, strategy: dict) -> List[dict]:
        """Autonomously search for candidates"""
        try:
            # For demo, we'll use existing candidates and apply search filters
            # In production, this would integrate with LinkedIn, Indeed, GitHub, etc.
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build search query based on strategy
            if "jd_id" in strategy:
                # Use existing JD for vector search
                cursor.execute("""
                    SELECT c.*, 1 - (c.embedding <=> jd.embedding) as similarity_score
                    FROM candidates c
                    CROSS JOIN job_descriptions jd
                    WHERE jd.id = %s AND c.embedding IS NOT NULL
                    ORDER BY c.embedding <=> jd.embedding
                    LIMIT 50
                """, (strategy["jd_id"],))
            else:
                # Use keyword-based search
                keywords = strategy.get("search_keywords", [])
                skills = strategy.get("required_skills", [])
                
                if keywords or skills:
                    query_parts = []
                    params = []
                    
                    if keywords:
                        keyword_conditions = " OR ".join(["raw_text ILIKE %s"] * len(keywords))
                        query_parts.append(f"({keyword_conditions})")
                        params.extend([f"%{kw}%" for kw in keywords])
                    
                    if skills:
                        skill_conditions = " OR ".join(["%s = ANY(skills)"] * len(skills))
                        query_parts.append(f"({skill_conditions})")
                        params.extend(skills)
                    
                    if query_parts:
                        where_clause = " OR ".join(query_parts)
                        cursor.execute(f"""
                            SELECT * FROM candidates 
                            WHERE {where_clause}
                            ORDER BY created_at DESC
                            LIMIT 50
                        """, params)
                    else:
                        cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC LIMIT 20")
                else:
                    cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC LIMIT 20")
            
            candidates = cursor.fetchall()
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(candidates)} candidates autonomously")
            return [dict(candidate) for candidate in candidates]
            
        except Exception as e:
            logger.error(f"Error searching candidates: {e}")
            return []
    
    async def rank_candidates_autonomously(self, goal_id: str, candidates: List[dict]) -> List[dict]:
        """Autonomously rank candidates using AI"""
        try:
            if not candidates:
                return []
            
            # Get the best matching JD for ranking
            strategy = await self.get_goal_strategy(goal_id)
            
            if "jd_id" in strategy:
                # Use existing ranking system
                response = requests.post(f"{API_URL}/rank-candidates", json={
                    "jd_id": strategy["jd_id"],
                    "limit": 10
                })
                
                if response.status_code == 200:
                    ranking_data = response.json()
                    return ranking_data.get("results", [])[:5]  # Top 5 for outreach
            
            # Fallback: Simple ranking based on skills and experience
            ranked_candidates = []
            for candidate in candidates[:10]:
                score = self.calculate_simple_score(candidate, strategy)
                if score > 0.3:  # Minimum threshold
                    ranked_candidates.append({
                        "candidate_id": candidate["id"],
                        "name": candidate["name"],
                        "email": candidate["email"],
                        "final_score": score,
                        "explanation": {
                            "matched_skills": [s for s in strategy.get("required_skills", []) if s in candidate.get("skills", [])],
                            "experience_match": min(candidate.get("total_years_experience", 0) / strategy.get("min_experience", 1), 1.0)
                        }
                    })
            
            return sorted(ranked_candidates, key=lambda x: x["final_score"], reverse=True)[:5]
            
        except Exception as e:
            logger.error(f"Error ranking candidates: {e}")
            return []
    
    async def send_autonomous_outreach(self, goal_id: str, candidates: List[dict]):
        """Send automated outreach to top candidates"""
        try:
            goal = await self.get_goal(goal_id)
            if not goal:
                return
            
            for candidate in candidates:
                # Create personalized outreach message
                message = self.generate_outreach_message(goal, candidate)
                
                # Log the outreach action
                await self.log_agent_action(goal_id, "send_outreach", {
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["name"],
                    "message": message,
                    "status": "sent"
                })
                
                logger.info(f"Sent autonomous outreach to {candidate['name']}")
                
        except Exception as e:
            logger.error(f"Error sending outreach: {e}")
    
    async def schedule_follow_ups(self, goal_id: str):
        """Schedule autonomous follow-up actions"""
        try:
            # Schedule follow-up in 3 days
            follow_up_time = datetime.now() + timedelta(days=3)
            
            await self.log_agent_action(goal_id, "schedule_follow_up", {
                "scheduled_time": follow_up_time.isoformat(),
                "action": "check_responses_and_follow_up"
            })
            
            logger.info(f"Scheduled follow-up for goal {goal_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling follow-up: {e}")
    
    def generate_outreach_message(self, goal: dict, candidate: dict) -> str:
        """Generate personalized outreach message"""
        matched_skills = candidate.get("explanation", {}).get("matched_skills", [])
        skill_text = ", ".join(matched_skills[:3]) if matched_skills else "your technical skills"
        
        return f"""
Hi {candidate['name']},

I hope this message finds you well. I'm reaching out because I believe your expertise in {skill_text} would be a great fit for an exciting opportunity we have.

We're looking for a {goal['title']} and I was impressed by your background. Based on your experience, I think you'd be an excellent candidate for this role.

Would you be interested in learning more about this opportunity? I'd love to schedule a brief conversation to discuss the details.

Best regards,
AI Hiring Agent
        """.strip()
    
    def calculate_simple_score(self, candidate: dict, strategy: dict) -> float:
        """Calculate simple matching score"""
        score = 0.0
        
        # Skill matching (50% weight)
        required_skills = strategy.get("required_skills", [])
        candidate_skills = candidate.get("skills", [])
        if required_skills:
            skill_overlap = len(set(required_skills) & set(candidate_skills)) / len(required_skills)
            score += 0.5 * skill_overlap
        
        # Experience matching (30% weight)
        min_exp = strategy.get("min_experience", 1)
        candidate_exp = candidate.get("total_years_experience", 0)
        if min_exp > 0:
            exp_ratio = min(candidate_exp / min_exp, 1.0)
            score += 0.3 * exp_ratio
        
        # Recent activity (20% weight)
        created_at = candidate.get("created_at")
        if created_at:
            days_old = (datetime.now() - datetime.fromisoformat(created_at.replace('Z', '+00:00'))).days
            recency_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
            score += 0.2 * recency_score
        
        return score
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        keywords = []
        text_lower = text.lower()
        
        tech_keywords = ["python", "javascript", "react", "node", "aws", "docker", "kubernetes", "postgresql", "mongodb"]
        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        return self.extract_keywords(text)  # Simplified for demo
    
    def infer_experience_level(self, text: str) -> str:
        """Infer experience level from text"""
        text_lower = text.lower()
        if "senior" in text_lower or "lead" in text_lower:
            return "senior"
        elif "junior" in text_lower or "entry" in text_lower:
            return "junior"
        else:
            return "mid"
    
    def extract_location_preferences(self, text: str) -> List[str]:
        """Extract location preferences from text"""
        locations = []
        text_lower = text.lower()
        
        if "remote" in text_lower:
            locations.append("Remote")
        if "san francisco" in text_lower or "sf" in text_lower:
            locations.append("San Francisco")
        if "new york" in text_lower or "nyc" in text_lower:
            locations.append("New York")
        
        return locations
    
    async def get_goal(self, goal_id: str) -> Optional[dict]:
        """Get goal details"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT * FROM agent_goals WHERE id = %s", (goal_id,))
            goal = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return dict(goal) if goal else None
            
        except Exception as e:
            logger.error(f"Error getting goal: {e}")
            return None
    
    async def get_goal_strategy(self, goal_id: str) -> dict:
        """Get goal strategy"""
        goal = await self.get_goal(goal_id)
        if goal:
            return await self.analyze_requirements(goal)
        return {}
    
    async def log_agent_action(self, goal_id: str, action_type: str, result: dict):
        """Log agent action"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            action_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO agent_actions (id, goal_id, action_type, status, result, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                action_id,
                goal_id,
                action_type,
                "completed",
                json.dumps(result),
                datetime.now()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging action: {e}")
    
    async def learn_from_feedback(self, feedback: CandidateFeedback):
        """Learn from candidate feedback to improve future decisions"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO candidate_feedback (candidate_id, feedback_type, feedback_score, notes, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                feedback.candidate_id,
                feedback.feedback_type,
                feedback.feedback_score,
                feedback.notes,
                feedback.created_at or datetime.now()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update learning data
            self.update_learning_model(feedback)
            
            logger.info(f"Learned from feedback for candidate {feedback.candidate_id}")
            
        except Exception as e:
            logger.error(f"Error learning from feedback: {e}")
    
    def update_learning_model(self, feedback: CandidateFeedback):
        """Update internal learning model based on feedback"""
        # Simplified learning - in production this would update ML models
        if feedback.feedback_type == "hired" and feedback.feedback_score > 0.8:
            logger.info("High-performing candidate hired - updating success patterns")
        elif feedback.feedback_type == "rejected" and feedback.feedback_score < 0.3:
            logger.info("Poor candidate rejected - updating rejection patterns")

# Initialize agent
agent = AIHiringAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent_id": agent.agent_id}

@app.post("/create-goal")
async def create_goal(goal_data: dict):
    """Create a new hiring goal for the agent"""
    try:
        goal_id = await agent.create_goal(goal_data)
        return {"status": "success", "goal_id": goal_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/goals")
async def get_goals():
    """Get all agent goals"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM agent_goals ORDER BY created_at DESC")
        goals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"goals": [dict(goal) for goal in goals]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/agent-actions/{goal_id}")
async def get_agent_actions(goal_id: str):
    """Get agent actions for a specific goal"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM agent_actions 
            WHERE goal_id = %s 
            ORDER BY created_at DESC
        """, (goal_id,))
        
        actions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {"actions": [dict(action) for action in actions]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/feedback")
async def submit_feedback(feedback: CandidateFeedback):
    """Submit feedback to help the agent learn"""
    try:
        await agent.learn_from_feedback(feedback)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/agent-status")
async def get_agent_status():
    """Get current agent status and activity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get active goals count
        cursor.execute("SELECT COUNT(*) as active_goals FROM agent_goals WHERE status = 'active'")
        active_goals = cursor.fetchone()["active_goals"]
        
        # Get recent actions count
        cursor.execute("""
            SELECT COUNT(*) as recent_actions 
            FROM agent_actions 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        recent_actions = cursor.fetchone()["recent_actions"]
        
        # Get total candidates contacted
        cursor.execute("""
            SELECT COUNT(*) as candidates_contacted 
            FROM agent_actions 
            WHERE action_type = 'send_outreach'
        """)
        candidates_contacted = cursor.fetchone()["candidates_contacted"]
        
        cursor.close()
        conn.close()
        
        return {
            "agent_id": agent.agent_id,
            "status": "active",
            "active_goals": active_goals,
            "recent_actions": recent_actions,
            "candidates_contacted": candidates_contacted,
            "last_action_time": agent.last_action_time.isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
