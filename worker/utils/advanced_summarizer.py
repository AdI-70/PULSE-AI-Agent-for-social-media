"""
Advanced multi-stage summarization with fact-checking for Pulse
"""

import structlog
import re
from typing import List, Dict, Any, Optional
import asyncio

logger = structlog.get_logger()


class Fact:
    """Represents a fact extracted from content."""
    
    def __init__(self, statement: str, source: str = "", confidence: float = 0.0):
        self.statement = statement
        self.source = source
        self.confidence = confidence


class AdvancedSummarizer:
    """Multi-stage summarization with fact-checking."""
    
    def __init__(self, llm_adapter):
        self.llm = llm_adapter
        logger.info("AdvancedSummarizer initialized")
    
    async def process(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Multi-stage summarization process.
        
        Args:
            article: Article dictionary with title, content, etc.
            
        Returns:
            Dictionary with refined summary, verified facts, and confidence score
        """
        try:
            logger.info("Starting multi-stage summarization", article_id=article.get("id"))
            
            # Stage 1: Initial summarization
            logger.info("Stage 1: Initial summarization")
            initial_summary = await self._initial_summarization(article)
            
            # Stage 2: Fact extraction and verification
            logger.info("Stage 2: Fact extraction and verification")
            facts = await self._extract_facts(initial_summary)
            verified_facts = await self._verify_facts(facts)
            
            # Stage 3: Refined summarization with verified facts
            logger.info("Stage 3: Refined summarization")
            refined_summary = await self._refine_summary(initial_summary, verified_facts, article)
            
            # Stage 4: Tone and style adjustment
            logger.info("Stage 4: Tone adjustment")
            final_summary = await self._adjust_tone(refined_summary, article)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(verified_facts)
            
            result = {
                "content": final_summary,
                "facts": [fact.__dict__ for fact in verified_facts],
                "confidence_score": confidence_score,
                "verification_status": "completed"
            }
            
            logger.info("Multi-stage summarization completed", confidence=confidence_score)
            return result
            
        except Exception as e:
            logger.error("Error in multi-stage summarization", error=str(e))
            # Fallback to basic summarization
            basic_summary = await self._basic_summarization(article)
            return {
                "content": basic_summary,
                "facts": [],
                "confidence_score": 0.5,
                "verification_status": "failed"
            }
    
    async def _initial_summarization(self, article: Dict[str, Any]) -> str:
        """Stage 1: Initial summarization."""
        title = article.get("title", "")
        content = article.get("content", "") or article.get("description", "")
        
        prompt = f"""
        Summarize the following article in 2-3 sentences:
        
        Title: {title}
        
        Content: {content[:2000]}  # Limit content length
        
        Summary:
        """
        
        summary = await self.llm.generate_text(prompt, max_tokens=300)
        return summary.strip()
    
    async def _extract_facts(self, summary: str) -> List[Fact]:
        """Stage 2: Extract factual statements from summary."""
        prompt = f"""
        Extract factual statements from the following text. Return each fact as a separate statement:
        
        Text: {summary}
        
        Facts:
        """
        
        facts_text = await self.llm.generate_text(prompt, max_tokens=500)
        fact_lines = facts_text.strip().split('\n')
        
        facts = []
        for line in fact_lines:
            line = line.strip()
            if line and not line.startswith(('Facts:', '-')):
                # Remove numbering if present
                line = re.sub(r'^\d+\.\s*', '', line)
                if line:
                    facts.append(Fact(statement=line, confidence=0.8))
        
        return facts
    
    async def _verify_facts(self, facts: List[Fact]) -> List[Fact]:
        """Stage 2: Verify facts (simplified implementation)."""
        verified_facts = []
        
        for fact in facts:
            try:
                # In a real implementation, this would check against trusted sources
                # For now, we'll simulate verification with confidence scoring
                
                # Check if fact contains numbers (more likely to be verifiable)
                has_numbers = bool(re.search(r'\d', fact.statement))
                
                # Check if fact contains superlatives (less likely to be accurate)
                has_superlatives = any(word in fact.statement.lower() for word in 
                                     ['best', 'worst', 'greatest', 'most', 'all', 'every'])
                
                # Adjust confidence based on these heuristics
                if has_numbers:
                    fact.confidence = min(1.0, fact.confidence + 0.1)
                if has_superlatives:
                    fact.confidence = max(0.0, fact.confidence - 0.2)
                
                # Only include facts with reasonable confidence
                if fact.confidence >= 0.6:
                    verified_facts.append(fact)
                    
            except Exception as e:
                logger.warning("Error verifying fact", error=str(e), fact=fact.statement)
                # Include with lower confidence
                fact.confidence = max(0.0, fact.confidence - 0.3)
                if fact.confidence >= 0.5:
                    verified_facts.append(fact)
        
        return verified_facts
    
    async def _refine_summary(self, initial_summary: str, verified_facts: List[Fact], article: Dict[str, Any]) -> str:
        """Stage 3: Refine summary with verified facts."""
        facts_text = "\n".join([f"- {fact.statement} (confidence: {fact.confidence:.2f})" 
                               for fact in verified_facts])
        
        prompt = f"""
        Refine the following summary by incorporating the verified facts:
        
        Original Summary: {initial_summary}
        
        Verified Facts:
        {facts_text}
        
        Article Title: {article.get('title', '')}
        
        Refined Summary:
        """
        
        refined_summary = await self.llm.generate_text(prompt, max_tokens=300)
        return refined_summary.strip()
    
    async def _adjust_tone(self, summary: str, article: Dict[str, Any]) -> str:
        """Stage 4: Adjust tone and style."""
        niche = article.get("niche", "technology")
        
        tone_instructions = {
            "technology": "Use a professional and informative tone",
            "business": "Use a business-appropriate tone with market insights",
            "science": "Use an educational and precise tone",
            "health": "Use a clear and reassuring tone",
            "entertainment": "Use an engaging and conversational tone"
        }
        
        tone_instruction = tone_instructions.get(niche, tone_instructions["technology"])
        
        prompt = f"""
        Adjust the tone of the following summary to be appropriate for the {niche} niche:
        
        Tone Instruction: {tone_instruction}
        
        Summary: {summary}
        
        Adjusted Summary:
        """
        
        adjusted_summary = await self.llm.generate_text(prompt, max_tokens=300)
        return adjusted_summary.strip()
    
    async def _basic_summarization(self, article: Dict[str, Any]) -> str:
        """Fallback basic summarization."""
        return await self.llm.summarize_article(
            title=article.get("title", ""),
            content=article.get("content", "") or article.get("description", ""),
            tone="professional"
        )
    
    def _calculate_confidence(self, verified_facts: List[Fact]) -> float:
        """Calculate overall confidence score based on verified facts."""
        if not verified_facts:
            return 0.5  # Neutral confidence
            
        # Average confidence of verified facts
        avg_confidence = sum(fact.confidence for fact in verified_facts) / len(verified_facts)
        
        # Boost confidence based on number of verified facts
        fact_count_bonus = min(0.2, len(verified_facts) * 0.05)
        
        # Final confidence score (clamped between 0 and 1)
        confidence = min(1.0, max(0.0, avg_confidence + fact_count_bonus))
        return confidence


# Global advanced summarizer instance
advanced_summarizer = None


def init_advanced_summarizer(llm_adapter):
    """Initialize the global advanced summarizer."""
    global advanced_summarizer
    advanced_summarizer = AdvancedSummarizer(llm_adapter)


def get_advanced_summarizer() -> AdvancedSummarizer:
    """Get the global advanced summarizer instance."""
    if advanced_summarizer is None:
        raise RuntimeError("Advanced summarizer not initialized")
    return advanced_summarizer