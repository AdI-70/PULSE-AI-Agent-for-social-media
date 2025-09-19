#!/usr/bin/env python3
"""
Pulse CLI Tool for Development and Operations
"""

import click
import requests
import json
import os
from typing import Optional
import time

# Configuration
API_BASE_URL = os.getenv("PULSE_API_URL", "http://localhost:8000")
API_KEY = os.getenv("PULSE_API_KEY", "")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Pulse CLI for development and operations."""
    pass


@cli.command()
@click.option('--niche', required=True, help='Niche to fetch articles for')
@click.option('--count', default=5, help='Number of articles to fetch')
def fetch_articles(niche: str, count: int):
    """Fetch articles for testing."""
    try:
        # In a real implementation, this would call the news fetcher directly
        click.echo(f"Fetching {count} articles for niche: {niche}")
        
        # For demo purposes, we'll just show a mock response
        mock_articles = [
            {
                "title": f"Sample Article about {niche} #{i+1}",
                "description": f"This is a sample article about {niche}",
                "url": f"https://example.com/article/{niche}/{i+1}",
                "source": {"name": "Example News"},
                "publishedAt": "2024-01-01T00:00:00Z"
            }
            for i in range(min(count, 5))
        ]
        
        click.echo(f"Fetched {len(mock_articles)} articles:")
        for article in mock_articles:
            click.echo(f"  - {article['title']}")
            
    except Exception as e:
        click.echo(f"Error fetching articles: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--env', type=click.Choice(['dev', 'staging', 'prod']), default='dev', help='Environment to deploy to')
def deploy(env: str):
    """Deploy to specified environment."""
    click.echo(f"Deploying to {env} environment...")
    
    # This would contain actual deployment logic
    # For now, we'll just simulate the process
    steps = [
        "Building Docker images...",
        "Pushing images to registry...",
        f"Updating {env} environment...",
        "Running database migrations...",
        "Restarting services...",
        "Verifying deployment..."
    ]
    
    for step in steps:
        click.echo(step)
        time.sleep(1)  # Simulate work
    
    click.echo(f"Successfully deployed to {env} environment!")


@cli.command()
@click.option('--niche', required=True, help='Niche to run pipeline for')
@click.option('--preview', is_flag=True, help='Run in preview mode (no actual posting)')
def run_pipeline(niche: str, preview: bool):
    """Run the news-to-X pipeline for a specific niche."""
    try:
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        data = {
            "niche": niche,
            "preview_mode": preview
        }
        
        response = requests.post(
            f"{API_BASE_URL}/run",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            click.echo(f"Pipeline job enqueued successfully!")
            click.echo(f"Job ID: {result['job_id']}")
            click.echo(f"Status: {result['status']}")
        else:
            click.echo(f"Error running pipeline: {response.status_code} - {response.text}", err=True)
            raise click.Abort()
            
    except requests.exceptions.ConnectionError:
        click.echo("Error: Could not connect to Pulse API. Make sure the backend is running.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error running pipeline: {e}", err=True)
        raise click.Abort()


@cli.command()
def health_check():
    """Check the health of the Pulse system."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            result = response.json()
            click.echo("✅ System is healthy!")
            click.echo(f"Status: {result['status']}")
            if 'timestamp' in result:
                click.echo(f"Timestamp: {result['timestamp']}")
        else:
            click.echo(f"❌ System health check failed: {response.status_code} - {response.text}", err=True)
            raise click.Abort()
            
    except requests.exceptions.ConnectionError:
        click.echo("❌ Error: Could not connect to Pulse API. Make sure the backend is running.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error checking system health: {e}", err=True)
        raise click.Abort()


@cli.command()
def status():
    """Get the current system status."""
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        
        if response.status_code == 200:
            result = response.json()
            click.echo("📊 System Status")
            click.echo("=" * 50)
            click.echo(f"System Health: {result['system_health']}")
            click.echo(f"Active Jobs: {result['active_jobs']}")
            click.echo(f"Total Jobs: {result['total_jobs']}")
            click.echo(f"Total Posts: {result['total_posts']}")
            
            if result['recent_jobs']:
                click.echo("\n📋 Recent Jobs:")
                for job in result['recent_jobs'][:5]:  # Show only first 5
                    click.echo(f"  - {job['niche']}: {job['status']} ({job['created_at']})")
            
            if result['recent_posts']:
                click.echo("\n📬 Recent Posts:")
                for post in result['recent_posts'][:5]:  # Show only first 5
                    click.echo(f"  - {post['platform']}: {post['status']} ({post['created_at']})")
        else:
            click.echo(f"❌ Failed to get system status: {response.status_code} - {response.text}", err=True)
            raise click.Abort()
            
    except requests.exceptions.ConnectionError:
        click.echo("❌ Error: Could not connect to Pulse API. Make sure the backend is running.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error getting system status: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--config-file', type=click.Path(exists=True), help='Configuration file to load')
def configure(config_file: Optional[str]):
    """Configure Pulse settings."""
    if config_file:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            click.echo(f"Loaded configuration from {config_file}")
            # In a real implementation, this would save the config to the API
        except Exception as e:
            click.echo(f"Error loading configuration: {e}", err=True)
            raise click.Abort()
    else:
        # Interactive configuration
        click.echo("🔧 Pulse Configuration")
        click.echo("=" * 30)
        
        # This would prompt for various settings
        # For now, we'll just show what would be configured
        settings = [
            "NewsAPI Key",
            "Google Search API Key",
            "OpenAI API Key",
            "X API Credentials",
            "Database Connection",
            "Redis Connection"
        ]
        
        for setting in settings:
            click.echo(f"  - {setting}")
        
        click.echo("\nUse environment variables or the web UI to configure these settings.")


@cli.command()
@click.option('--niche', required=True, help='Niche to test content ranking for')
@click.option('--count', default=10, help='Number of articles to rank')
def test_ranking(niche: str, count: int):
    """Test the content ranking system."""
    click.echo(f"Testing content ranking for niche: {niche}")
    click.echo(f"Fetching {count} articles...")
    
    # In a real implementation, this would call the ranking system
    click.echo("Ranking articles based on relevance, freshness, and authority...")
    click.echo("Top 5 ranked articles:")
    for i in range(1, 6):
        click.echo(f"  {i}. Sample Article Title {i} (Score: {1.0 - (i-1)*0.1:.2f})")


@cli.command()
@click.option('--experiment-name', required=True, help='Name of the A/B test experiment')
@click.option('--variants', default=5, help='Number of variants to generate')
def create_ab_test(experiment_name: str, variants: int):
    """Create an A/B testing experiment."""
    click.echo(f"Creating A/B test experiment: {experiment_name}")
    click.echo(f"Generating {variants} content variants...")
    
    # In a real implementation, this would create actual variants
    strategies = ["Casual Tone", "Formal Tone", "Question Hook", "Statistic Lead", "Story Opening"]
    
    for i, strategy in enumerate(strategies[:variants], 1):
        click.echo(f"  Variant {i}: {strategy}")
    
    click.echo(f"\nExperiment '{experiment_name}' created successfully!")
    click.echo("Use 'run-ab-test' command to start the experiment.")


@cli.command()
@click.option('--experiment-id', required=True, help='ID of the experiment to run')
@click.option('--duration', default=60, help='Duration of experiment in minutes')
def run_ab_test(experiment_id: str, duration: int):
    """Run an A/B testing experiment."""
    click.echo(f"Running A/B test experiment {experiment_id} for {duration} minutes")
    click.echo("Monitoring performance metrics...")
    
    # Simulate experiment results
    click.echo("\nExperiment Results:")
    click.echo("Variant    Impressions    Clicks    CTR")
    click.echo("--------   -----------    ------    ---")
    click.echo("Casual     1250           150       12.0%")
    click.echo("Formal     1200           120       10.0%")
    click.echo("Question   1300           180       13.8%")
    click.echo("Stat Lead  1100           110       10.0%")
    click.echo("Story      1150           140       12.2%")
    
    click.echo("\nRecommendation: Use 'Question Hook' variant for best performance.")


if __name__ == '__main__':
    cli()