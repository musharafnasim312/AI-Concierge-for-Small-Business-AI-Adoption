from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FeedbackScore(BaseModel):
    score: float
    timestamp: datetime = datetime.now()

class SelfReflection:
    def __init__(self, decay_factor: float = 0.5):
        self.feedback_scores: List[FeedbackScore] = []
        self.decay_factor = decay_factor
    
    def add_feedback(self, is_good: bool):
        """Add feedback score (+1 for good, -1 for bad)"""
        score = 1.0 if is_good else -1.0
        self.feedback_scores.append(FeedbackScore(score=score))
    
    def get_cumulative_score(self) -> float:
        """Calculate cumulative score with decay"""
        if not self.feedback_scores:
            return 0.0
        
        current_time = datetime.now()
        cumulative = 0.0
        
        for feedback in self.feedback_scores:
            turns_passed = (current_time - feedback.timestamp).total_seconds() / 60  # minutes
            decayed_score = feedback.score * (self.decay_factor ** turns_passed)
            cumulative += decayed_score
        
        return cumulative
    
    def get_prompt_modifier(self) -> Optional[str]:
        """Get prompt modification based on cumulative score"""
        score = self.get_cumulative_score()
        if score < 0:
            return "Be more concise and cite sources explicitly."
        elif score > 0:
            return "Maintain current style, user is satisfied."
        return None

# Global instance
reflection = SelfReflection()
