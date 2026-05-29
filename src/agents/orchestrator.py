"""
src/agents/orchestrator.py
Deterministic Rules & Scoring Engine.

Evaluates game state natively to save VRAM and prevent LLM hallucinations.
"""

from typing import Dict, Any
from ..config import SCORING_WEIGHTS
from ..utils.logger import setup_logger

logger = setup_logger("agents.orchestrator")

class OrchestratorAgent:
    """Pure Python Orchestrator. No LLM overhead."""
    
    def __init__(self):
        self.total_red_score = 0
        self.total_blue_score = 0
        self.round_history = []
        logger.info("Deterministic Orchestrator initialized. VRAM preserved.")

    def _calculate_creativity_multiplier(self, variant: str, detection_score: int) -> float:
        """The mathematical bridge between human creativity and cyber mechanics."""
        if variant == "heist_movie" and detection_score <= 3:
            return 1.5  
        elif variant == "chaos_gremlin" and detection_score >= 8:
            return 1.5  
        elif variant == "inside_man":
            return 1.2  
        elif variant == "lazy_attacker" and detection_score > 5:
            return 0.8  
        return 1.0

    def evaluate_round(self, state: Dict[str, Any], simulator) -> Dict[str, Any]:
        """Calculates scores based strictly on simulator action logs."""
        round_num = state.get("round_number", 1)
        posture = simulator.get_security_posture()
        
        red_points = 0
        blue_points = 0
        
        recent_actions = simulator.action_log[-6:] if simulator.action_log else []
        
        for action in recent_actions:
            if action.agent == "red" and action.success:
                base_points = 0
                if action.action_type == "exploit_service":
                    base_points = SCORING_WEIGHTS.get("host_compromised", 10)
                elif action.action_type == "establish_persistence":
                    base_points = SCORING_WEIGHTS.get("persistence_established", 15)
                elif action.action_type == "lateral_move":
                    base_points = SCORING_WEIGHTS.get("lateral_movement", 5)

                multiplier = self._calculate_creativity_multiplier(
                    action.creativity_type or "standard", 
                    action.detection_score
                )
                red_points += int(base_points * multiplier)
            
            elif action.agent == "blue" and action.success:
                if action.action_type == "detect_anomaly":
                    stealth_bonus = max(0, 10 - action.detection_score)
                    blue_points += SCORING_WEIGHTS.get("detection", 5) + stealth_bonus
                elif action.action_type == "patch_vulnerability":
                    blue_points += SCORING_WEIGHTS.get("successful_patch", 10)

        self.total_red_score += red_points
        self.total_blue_score += blue_points
        
        current_state = simulator.get_state()
        current_state.red_score = self.total_red_score
        current_state.blue_score = self.total_blue_score
        
        all_compromised = posture.get("compromised_hosts", 0) >= posture.get("total_hosts", 4)
        should_continue = not all_compromised
        
        winner = None
        if all_compromised:
            winner = "red"
            logger.info("Simulation Terminated: Red Team compromised all hosts.")

        self.round_history.append({
            "round": round_num,
            "red_points": red_points,
            "blue_points": blue_points,
            "red_total": self.total_red_score,
            "blue_total": self.total_blue_score,
            "compromised_hosts": posture.get("compromised_hosts", 0)
        })
        
        logger.info(f"Round {round_num} Eval → Red +{red_points} (Total: {self.total_red_score}) | Blue +{blue_points} (Total: {self.total_blue_score})")

        return {
            "continue_simulation": should_continue,
            "winner": winner,
            "red_points": red_points,
            "blue_points": blue_points
        }

    def get_final_results(self, simulator) -> Dict[str, Any]:
        """Summarizes the match for final JSON export."""
        posture = simulator.get_security_posture()
        
        winner = "draw"
        if self.total_red_score > self.total_blue_score:
            winner = "red"
        elif self.total_blue_score > self.total_red_score:
            winner = "blue"
            
        return {
            "winner": winner,
            "red_score": self.total_red_score,
            "blue_score": self.total_blue_score,
            "total_rounds": len(self.round_history),
            "final_state": posture
        }
