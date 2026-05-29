"""Orchestrator agent with fixed scoring persistence."""
from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from ..config import get_model_config, SCORING_WEIGHTS
from ..utils.prompts import ORCHESTRATOR_PROMPT
from ..utils.logger import setup_logger
from ..utils.json_parser import safe_parse_llm_response

logger = setup_logger("agents.orchestrator")

class OrchestratorAgent:
    def __init__(self, model_name: str = None):
        config = get_model_config("orchestrator")
        self.model_name = model_name or config["model"]
        self.llm = ChatOllama(**config)
        self.total_red_score = 0
        self.total_blue_score = 0
        self.round_history = []
        logger.info(f"Orchestrator: {self.model_name}")
    
    def evaluate_round(self, state: Dict, simulator) -> Dict[str, Any]:
        posture = simulator.get_security_posture()
        
        prompt = ORCHESTRATOR_PROMPT.format(
            round_number=state.get("round_number", 1),
            red_action=state.get("red_decision", {}).get("action", "unknown"),
            blue_action=state.get("blue_decision", {}).get("action", "unknown"),
            red_result=str(state.get("red_decision", {}).get("result", {}))[:150],
            blue_result=str(state.get("blue_decision", {}).get("result", {}))[:150],
            compromised_count=posture.get("compromised_hosts", 0),
            total_hosts=posture.get("total_hosts", 4),
            alert_count=len(simulator.alerts),
            patches=posture.get("patched_services", 0)
        )
        
        try:
            response = self.llm.invoke([SystemMessage(content=prompt)])
            decision = safe_parse_llm_response(response.content, default={
                "outcome": "neutral",
                "red_points": 8,
                "blue_points": 6,
                "continue_simulation": True,
                "reasoning": "Default",
                "key_observation": "Continue"
            })
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            decision = {
                "outcome": "neutral",
                "red_points": 5,
                "blue_points": 5,
                "continue_simulation": True,
                "reasoning": "Error fallback"
            }
        
        # Calculate actual scores from results
        red_result = state.get("red_decision", {}).get("result", {})
        blue_result = state.get("blue_decision", {}).get("result", {})
        
        red_points = decision.get("red_points", 0)
        blue_points = decision.get("blue_points", 0)
        
        # Validate and adjust based on actual outcomes
        if red_result.get("success"):
            if red_result.get("host_compromised"):
                red_points = max(red_points, SCORING_WEIGHTS["host_compromised"])
            if red_result.get("persistence_established"):
                red_points = max(red_points, SCORING_WEIGHTS["persistence_established"])
        
        if blue_result.get("success"):
            if blue_result.get("compromised_hosts_detected"):
                blue_points = max(blue_points, 8)
            if blue_result.get("service_patched"):
                blue_points = max(blue_points, SCORING_WEIGHTS["successful_patch"])
        
        # CRITICAL FIX: Persist scores to simulator state
        self.total_red_score += red_points
        self.total_blue_score += blue_points
        
        current_state = simulator.get_state()
        current_state.red_score = self.total_red_score
        current_state.blue_score = self.total_blue_score
        
        # Store in history
        self.round_history.append({
            "round": state.get("round_number"),
            "red_points": red_points,
            "blue_points": blue_points,
            "red_total": self.total_red_score,
            "blue_total": self.total_blue_score
        })
        
        logger.info(f"Round {state.get('round_number')}: Red +{red_points} (total: {self.total_red_score}), Blue +{blue_points} (total: {self.total_blue_score})")
        
        return {
            **decision,
            "red_points": red_points,
            "blue_points": blue_points,
            "red_total": self.total_red_score,
            "blue_total": self.total_blue_score
        }
    
    def get_final_results(self, simulator) -> Dict[str, Any]:
        posture = simulator.get_security_posture()
        
        return {
            "winner": "red" if self.total_red_score > self.total_blue_score else "blue" if self.total_blue_score > self.total_red_score else "draw",
            "red_score": self.total_red_score,
            "blue_score": self.total_blue_score,
            "total_rounds": len(self.round_history),
            "final_state": posture
        }
