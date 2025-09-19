-- Advanced database optimizations for Pulse

-- 1. Composite index for article queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_niche_status_created 
ON articles(niche, status, created_at DESC) 
WHERE deleted_at IS NULL;

-- 2. Index for content deduplication
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_content_hash 
ON articles(content_hash) 
WHERE content_hash IS NOT NULL;

-- 3. Index for source-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_source 
ON articles(source, published_at DESC);

-- 4. Index for job status queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_status 
ON jobs(status, created_at DESC);

-- 5. Index for post status queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_status 
ON posts(status, created_at DESC);

-- 6. Partitioning for articles table (example for monthly partitioning)
-- Note: This would be implemented when the table grows significantly
/*
CREATE TABLE articles_202401 PARTITION OF articles
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE articles_202402 PARTITION OF articles
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
*/

-- 7. Materialized view for daily statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_article_stats AS
SELECT 
    DATE(created_at) as date,
    niche,
    COUNT(*) as article_count,
    COUNT(CASE WHEN status = 'published' THEN 1 END) as published_count,
    AVG(LENGTH(content)) as avg_content_length,
    COUNT(DISTINCT source) as unique_sources
FROM articles
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), niche
WITH DATA;

-- 8. Index for the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_article_stats 
ON daily_article_stats (date, niche);

-- 9. Materialized view for job performance
CREATE MATERIALIZED VIEW IF NOT EXISTS job_performance_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM jobs
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
WITH DATA;

-- 10. Index for job performance view
CREATE UNIQUE INDEX IF NOT EXISTS idx_job_performance_stats 
ON job_performance_stats (date);

-- 11. Refresh functions for materialized views
CREATE OR REPLACE FUNCTION refresh_daily_article_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_article_stats;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_job_performance_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY job_performance_stats;
END;
$$ LANGUAGE plpgsql;

-- 12. Scheduled refresh (would be handled by a cron job or similar)
-- Example cron job entries:
-- 0 2 * * * psql -U pulse_user -d pulse_db -c "SELECT refresh_daily_article_stats();"
-- 0 3 * * * psql -U pulse_user -d pulse_db -c "SELECT refresh_job_performance_stats();"