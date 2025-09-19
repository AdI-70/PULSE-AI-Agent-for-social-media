"""
A/B Testing Framework for Pulse Content Optimization
"""

import structlog
import random
import hashlib
from typing import List, Dict, Any, Optional
from enum import Enum

logger = structlog.get_logger()


class VariantStrategy(Enum):
    """Different strategies for creating content variants."""
    CASUAL_TONE = "casual_tone"
    FORMAL_TONE = "formal_tone"
    QUESTION_HOOK = "question_hook"
    STATISTIC_LEAD = "statistic_lead"
    STORY_OPENING = "story_opening"


class Variant:
    """Represents a content variant for A/B testing."""
    
    def __init__(self, content: str, strategy: VariantStrategy, weight: float = 1.0):
        self.content = content
        self.strategy = strategy
        self.weight = weight
        self.impressions = 0
        self.clicks = 0
        self.conversions = 0
    
    @property
    def ctr(self) -> float:
        """Click-through rate."""
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions
    
    @property
    def conversion_rate(self) -> float:
        """Conversion rate."""
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions


class ABTestingEngine:
    """A/B testing engine for content optimization."""
    
    def __init__(self):
        self.experiments = {}
        self.variants = {}
        logger.info("ABTestingEngine initialized")
    
    def create_experiment(self, name: str, variants: List[Variant]) -> str:
        """
        Create a new A/B testing experiment.
        
        Args:
            name: Name of the experiment
            variants: List of content variants to test
            
        Returns:
            Experiment ID
        """
        experiment_id = hashlib.md5(name.encode()).hexdigest()[:8]
        
        self.experiments[experiment_id] = {
            "name": name,
            "variants": {i: variant for i, variant in enumerate(variants)},
            "created_at": None  # Would be set to current time in real implementation
        }
        
        logger.info("Created A/B test experiment", experiment_id=experiment_id, name=name, 
                   variant_count=len(variants))
        return experiment_id
    
    def run_experiment(self, content: str, experiment_id: str, user_id: Optional[str] = None) -> Variant:
        """
        Run an experiment and select a variant.
        
        Args:
            content: Original content
            experiment_id: ID of the experiment to run
            user_id: Optional user ID for consistent variant assignment
            
        Returns:
            Selected variant
        """
        if experiment_id not in self.experiments:
            logger.warning("Experiment not found, returning original content", experiment_id=experiment_id)
            return Variant(content, VariantStrategy.CASUAL_TONE)
        
        experiment = self.experiments[experiment_id]
        variants = list(experiment["variants"].values())
        
        # Select variant based on weights
        selected_variant = self._weighted_random_selection(variants)
        
        # Track impression
        selected_variant.impressions += 1
        
        logger.debug("Selected variant for A/B test", experiment_id=experiment_id, 
                    strategy=selected_variant.strategy.value)
        return selected_variant
    
    def generate_variants(self, content: str) -> List[Variant]:
        """
        Generate multiple variants of content.
        
        Args:
            content: Original content
            
        Returns:
            List of content variants
        """
        variants = [
            self._create_variant(content, VariantStrategy.CASUAL_TONE),
            self._create_variant(content, VariantStrategy.FORMAL_TONE),
            self._create_variant(content, VariantStrategy.QUESTION_HOOK),
            self._create_variant(content, VariantStrategy.STATISTIC_LEAD),
            self._create_variant(content, VariantStrategy.STORY_OPENING)
        ]
        
        logger.info("Generated content variants", variant_count=len(variants))
        return variants
    
    def _create_variant(self, content: str, strategy: VariantStrategy) -> Variant:
        """Create a variant based on the specified strategy."""
        # In a real implementation, this would use an LLM to generate variants
        # For now, we'll simulate different transformations
        
        if strategy == VariantStrategy.CASUAL_TONE:
            variant_content = f"Hey! Check this out: {content.lower()}"
        elif strategy == VariantStrategy.FORMAL_TONE:
            variant_content = f"Important update: {content}"
        elif strategy == VariantStrategy.QUESTION_HOOK:
            variant_content = f"Did you know? {content} What do you think?"
        elif strategy == VariantStrategy.STATISTIC_LEAD:
            variant_content = f"New data shows: {content}"
        elif strategy == VariantStrategy.STORY_OPENING:
            variant_content = f"Here's a story for you: {content}"
        else:
            variant_content = content
        
        return Variant(variant_content, strategy)
    
    def _weighted_random_selection(self, variants: List[Variant]) -> Variant:
        """Select a variant based on weights."""
        total_weight = sum(variant.weight for variant in variants)
        random_value = random.uniform(0, total_weight)
        
        current_weight = 0
        for variant in variants:
            current_weight += variant.weight
            if random_value <= current_weight:
                return variant
        
        # Fallback to first variant
        return variants[0]
    
    def record_interaction(self, variant: Variant, interaction_type: str):
        """
        Record user interaction with a variant.
        
        Args:
            variant: The variant that was shown
            interaction_type: Type of interaction ('click', 'conversion', etc.)
        """
        if interaction_type == 'click':
            variant.clicks += 1
        elif interaction_type == 'conversion':
            variant.conversions += 1
        
        logger.debug("Recorded interaction", strategy=variant.strategy.value, 
                    interaction_type=interaction_type)
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get results for an experiment.
        
        Args:
            experiment_id: ID of the experiment
            
        Returns:
            Experiment results
        """
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}
        
        experiment = self.experiments[experiment_id]
        variants = experiment["variants"]
        
        results = {
            "experiment_id": experiment_id,
            "name": experiment["name"],
            "variants": {}
        }
        
        for i, variant in variants.items():
            results["variants"][variant.strategy.value] = {
                "impressions": variant.impressions,
                "clicks": variant.clicks,
                "conversions": variant.conversions,
                "ctr": variant.ctr,
                "conversion_rate": variant.conversion_rate
            }
        
        logger.info("Retrieved experiment results", experiment_id=experiment_id)
        return results


# Global A/B testing engine instance
ab_testing_engine = None


def init_ab_testing_engine():
    """Initialize the global A/B testing engine."""
    global ab_testing_engine
    ab_testing_engine = ABTestingEngine()


def get_ab_testing_engine() -> ABTestingEngine:
    """Get the global A/B testing engine instance."""
    if ab_testing_engine is None:
        raise RuntimeError("A/B testing engine not initialized")
    return ab_testing_engine