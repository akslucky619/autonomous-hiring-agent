-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create candidates table
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    email TEXT,
    location TEXT,
    work_authorization TEXT,
    total_years_experience NUMERIC,
    skills TEXT[],
    raw_text TEXT,
    embedding VECTOR(768),
    structured_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create job_descriptions table
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    location TEXT,
    required_skills TEXT[],
    optional_skills TEXT[],
    min_years_experience NUMERIC,
    raw_text TEXT,
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create agent goals table
CREATE TABLE agent_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    target_positions INTEGER DEFAULT 1,
    deadline TIMESTAMPTZ,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create agent actions table
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES agent_goals(id),
    action_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create candidate feedback table
CREATE TABLE candidate_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID REFERENCES candidates(id),
    feedback_type TEXT NOT NULL,
    feedback_score NUMERIC,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX ON candidates USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON candidates USING GIN (skills);
CREATE INDEX ON job_descriptions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON job_descriptions USING GIN (required_skills);
CREATE INDEX ON agent_actions (goal_id);
CREATE INDEX ON agent_actions (action_type);
CREATE INDEX ON agent_actions (created_at);
CREATE INDEX ON candidate_feedback (candidate_id);
CREATE INDEX ON candidate_feedback (feedback_type);

-- Insert sample job description
INSERT INTO job_descriptions (title, location, required_skills, optional_skills, min_years_experience, raw_text) VALUES (
    'Senior Python Developer',
    'Remote',
    ARRAY['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
    ARRAY['AWS', 'Redis', 'GraphQL', 'Machine Learning'],
    3,
    'We are looking for a Senior Python Developer to join our team. You will work on building scalable APIs using FastAPI and PostgreSQL. Experience with Docker and cloud platforms is preferred. This is a remote position with competitive compensation.'
);
