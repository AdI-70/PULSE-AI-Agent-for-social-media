export interface PipelineConfig {
  id?: number
  niches: string[]
  frequency: string
  tone: string
  auto_post: boolean
  created_at?: string
  updated_at?: string
}

export interface JobStatus {
  job_id: string
  niche: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  result?: {
    articles_fetched: number
    articles_processed: number
    posts_created: number
    posts_published: number
    errors: string[]
  }
}

export interface PostStatus {
  id: number
  content: string
  platform: string
  status: 'pending' | 'posted' | 'failed'
  posted_at?: string
  created_at: string
  error_message?: string
  engagement_stats?: Record<string, any>
}

export interface SystemStatus {
  system_health: 'healthy' | 'busy' | 'degraded'
  active_jobs: number
  total_jobs: number
  total_posts: number
  recent_jobs: JobStatus[]
  recent_posts: PostStatus[]
  current_config?: Record<string, any>
}

export interface RunRequest {
  niche: string
  preview_mode?: boolean
}

export interface RunResponse {
  job_id: string
  niche: string
  status: string
  message: string
}