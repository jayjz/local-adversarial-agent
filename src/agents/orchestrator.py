"""
src/agents/orchestrator.py
Deterministic Rules Engine.

Evaluates game state, calculates scores natively (saving VRAM), 
and determines win conditions without relying on LLM hallucinations.
"""

from typing import Dict, Any
from ..config import SCORING_WEIGHTS
from ..utils.logger import setup_logger

logger = setup_logger("agents.orchestrator")

class OrchestratorAgent:
    """
    Pure Python Orchestrator. No LLM overhead.
    """
    def __init__(self):
        self.total_red_score = 0
        self.total_blue_score = 0
        self.round_history = []
        logger.info("Deterministic Orchestrator initialized. VRAM preserved.")
    
    def evaluate_round(self, state: Dict[str, Any], simulator) -> Dict[str, Any]:
        """
        Calculates scores based strictly on the simulator's action logs for the current round.
        """
        round_num = state.get("round_number", 1)
        posture = simulator.get_security_posture()
        
        # Initialize round points
        red_points = 0
        blue_points = 0
        
        # Analyze the latest actions from the simulator log
        # Assuming simulator logs have a 'success' flag and 'action_type'
        recent_actions = simulator.action_log[-4:] if simulator.action_log else []
        
        for action in recent_actions:
            if action.agent == "red" and action.success:
                if action.action_type == "exploit_service":
                    red_points += SCORING_WEIGHTS.get("host_compromised", 10)
                elif action.action_type == "establish_persistence":
                    red_points += SCORING_WEIGHTS.get("persistence_established", 15)
                elif action.action_type == "lateral_move":
                    red_points += SCORING_WEIGHTS.get("lateral_movement", 5)
            
            elif action.agent == "blue" and action.success:
                if action.action_type == "detect_anomaly":
                    blue_points += SCORING_WEIGHTS.get("detection", 5)
                elif action.action_type == "patch_vulnerability":
                    blue_points += SCORING_WEIGHTS.get("successful_patch", 10)

        # Update global scores
        self.total_red_score += red_points
        self.total_blue_score += blue_points
        
        # Persist to simulator state properly
        current_state = simulator.get_state()
        current_state.red_score = self.total_red_score
        current_state.blue_score = self.total_blue_score
        
        # Store in history for UI / Data Annotation Export
        self.round_history.append({
            "round": round_num,
            "red_points": red_points,
            "blue_points": blue_points,
            "red_total": self.total_red_score,
            "blue_total": self.total_blue_score,
            "compromised_hosts": posture.get("compromised_hosts", 0)
        })
        
        logger.info(f"Round {round_num} Evaluation → Red +{red_points} (Total: {self.total_red_score}) | Blue +{blue_points} (Total: {self.total_blue_score})")
        
        # Determine if simulation should continue
        all_compromised = posture.get("compromised_hosts", 0) >= posture.get("total_hosts", 4)
        should_continue = not all_compromised
        
        winner = None
        if all_compromised:
            winner = "red"
            logger.info("Simulation Terminated: Red Team compromised all hosts.")

        return {
            "continue_simulation": should_continue,
            "winner": winner,
            "red_points": red_points,
            "blue_points": blue_points
        }

    def get_final_results(self, simulator) -> Dict[str, Any]:
        """Called at the end of the simulation to summarize."""
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
