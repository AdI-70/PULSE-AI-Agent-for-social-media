-- Initialize Pulse database

-- Create tables first
CREATE TABLE IF NOT EXISTS pipeline_configs (
    id SERIAL PRIMARY KEY,
    niches JSON,
    frequency VARCHAR(50),
    tone VARCHAR(50),
    auto_post BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content TEXT,
    url VARCHAR(500) NOT NULL UNIQUE,
    source VARCHAR(100),
    author VARCHAR(200),
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW(),
    niche VARCHAR(100),
    content_hash VARCHAR(64) UNIQUE
);

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    platform VARCHAR(50) DEFAULT 'x',
    post_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT,
    engagement_stats JSON
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE,
    niche VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    result JSON
);

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_articles_niche ON articles(niche);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at trigger to pipeline_configs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_pipeline_configs_updated_at'
    ) THEN
        CREATE TRIGGER update_pipeline_configs_updated_at 
            BEFORE UPDATE ON pipeline_configs 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

-- Insert default configuration if none exists
INSERT INTO pipeline_configs (niches, frequency, tone, auto_post)
VALUES 
    ('["technology", "artificial intelligence"]'::json, 'hourly', 'professional', false)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pulse_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pulse_user;