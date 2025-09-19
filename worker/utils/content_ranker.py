"""
Advanced content ranking system for Pulse
"""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math

logger = structlog.get_logger()


class ContentRanker:
    """ML-based content ranking system."""
    
    def __init__(self):
        # In a real implementation, this would load an actual ML model
        self.model = None
        logger.info("ContentRanker initialized")
    
    def rank_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank articles based on multiple factors.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of articles sorted by rank score (highest first)
        """
        try:
            ranked_articles = []
            for article in articles:
                score = self.calculate_composite_score(article)
                article['rank_score'] = score
                ranked_articles.append(article)
            
            # Sort by rank score (highest first)
            ranked_articles.sort(key=lambda x: x['rank_score'], reverse=True)
            return ranked_articles
            
        except Exception as e:
            logger.error("Error ranking articles", error=str(e))
            # Return articles in original order if ranking fails
            return articles
    
    def calculate_composite_score(self, article: Dict[str, Any]) -> float:
        """
        Calculate a composite score for an article based on multiple factors.
        
        Args:
            article: Article dictionary
            
        Returns:
            Composite score (0.0 to 1.0)
        """
        try:
            # Extract article features
            title = article.get('title', '')
            description = article.get('description', '')
            content = article.get('content', '')
            source = article.get('source', {}).get('name', '')
            published_at = article.get('publishedAt')
            
            # Calculate individual scores
            relevance_score = self._calculate_relevance_score(title, description, content)
            freshness_score = self._calculate_freshness_score(published_at)
            source_authority_score = self._calculate_source_authority(source)
            engagement_potential_score = self._calculate_engagement_potential(title, description)
            
            # Weighted composite score
            composite_score = (
                relevance_score * 0.4 +
                freshness_score * 0.3 +
                source_authority_score * 0.2 +
                engagement_potential_score * 0.1
            )
            
            return min(1.0, max(0.0, composite_score))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error("Error calculating composite score", error=str(e))
            return 0.5  # Return neutral score on error
    
    def _calculate_relevance_score(self, title: str, description: str, content: str) -> float:
        """Calculate relevance score based on content quality."""
        # Simple heuristic-based scoring
        # In a real implementation, this would use an ML model
        
        # Length-based scoring (optimal length is 50-200 words for title+description)
        title_desc_length = len((title + " " + description).split())
        length_score = 1.0 - abs(100 - title_desc_length) / 100.0
        length_score = max(0.0, min(1.0, length_score))
        
        # Keyword density scoring (simplified)
        keywords = ['ai', 'artificial intelligence', 'machine learning', 'technology', 'innovation']
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in (title + " " + description).lower())
        keyword_score = min(1.0, keyword_count / 3.0)
        
        # Content quality scoring (simplified)
        content_length = len(content.split())
        quality_score = min(1.0, content_length / 500.0)  # Assume 500 words is good
        
        return (length_score * 0.4 + keyword_score * 0.3 + quality_score * 0.3)
    
    def _calculate_freshness_score(self, published_at: Optional[str]) -> float:
        """Calculate freshness score based on publication time."""
        if not published_at:
            return 0.5  # Neutral score if no publication time
        
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            now = datetime.now(pub_date.tzinfo)
            age_hours = (now - pub_date).total_seconds() / 3600
            
            # Score decreases exponentially with age (newer is better)
            # Articles from last 24 hours get high scores, older articles get lower scores
            freshness_score = math.exp(-age_hours / 24.0)
            return max(0.0, min(1.0, freshness_score))
            
        except Exception as e:
            logger.warning("Error calculating freshness score", error=str(e))
            return 0.5  # Neutral score on error
    
    def _calculate_source_authority(self, source: str) -> float:
        """Calculate source authority score."""
        # In a real implementation, this would use a database of source reputations
        high_authority_sources = [
            'techcrunch', 'the verge', 'wired', 'ars technica', 'reuters', 
            'associated press', 'bloomberg', 'wall street journal', 'new york times'
        ]
        
        source_lower = source.lower()
        for authority_source in high_authority_sources:
            if authority_source in source_lower:
                return 1.0
        
        # Medium authority sources
        medium_authority_sources = [
            'medium', 'github', 'stackoverflow', 'reddit'
        ]
        
        for medium_source in medium_authority_sources:
            if medium_source in source_lower:
                return 0.7
        
        # Unknown sources get a moderate score
        return 0.5
    
    def _calculate_engagement_potential(self, title: str, description: str) -> float:
        """Calculate potential for engagement based on title and description."""
        text = (title + " " + description).lower()
        
        # Engagement-inducing elements
        question_words = ['how', 'what', 'why', 'when', 'where', 'which', 'who', 'can', 'could', 'would', 'should']
        has_question = any(word in text for word in question_words)
        
        # Strong action words
        action_words = ['breakthrough', 'revolutionary', 'shocking', 'amazing', 'incredible', 'unbelievable']
        has_action = any(word in text for word in action_words)
        
        # Numbers (people love lists and statistics)
        has_number = any(char.isdigit() for char in text)
        
        # Exclamation marks (enthusiasm)
        exclamation_count = text.count('!')
        
        # Calculate score
        score = 0.0
        if has_question:
            score += 0.2
        if has_action:
            score += 0.2
        if has_number:
            score += 0.2
        score += min(0.2, exclamation_count * 0.05)  # Cap exclamation contribution
        
        return min(1.0, score)


# Global content ranker instance
content_ranker = ContentRanker()


def get_content_ranker() -> ContentRanker:
    """Get the global content ranker instance."""
    return content_ranker