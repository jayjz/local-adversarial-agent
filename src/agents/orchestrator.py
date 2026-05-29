"""
Orchestrator Agent - Manages simulation flow and judges outcomes.
Makes decisions about round progression, scoring, and win conditions.
"""

import json
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import get_model_config, OLLAMA_BASE_URL, MAX_ROUNDS, SCORING_WEIGHTS
from ..utils.prompts import ORCHESTRATOR_PROMPT
from ..utils.logger import setup_logger

logger = setup_logger("agents.orchestrator")


class OrchestratorAgent:
    """Orchestrates the red vs blue simulation, judges rounds, and tracks state."""
    
    def __init__(self, model_name: str = None):
        """Initialize orchestrator with Ollama model."""
        config = get_model_config("orchestrator")
        self.model_name = model_name or config["model"]
        
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=config["temperature"],
            top_p=config["top_p"],
            num_ctx=config["num_ctx"],
        )
        
        self.round_history = []
        logger.info(f"Orchestrator initialized with model: {self.model_name}")
    
    def evaluate_round(self, simulator, round_num: int,
                      red_action: Dict[str, Any], red_result: Dict[str, Any],
                      blue_action: Dict[str, Any], blue_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the outcome of a round and update scores.
        
        Args:
            simulator: NetworkSimulator instance
            round_num: Current round number
            red_action: Red team action taken
            red_result: Result of red team action
            blue_action: Blue team action taken
            blue_result: Result of blue team action
        
        Returns:
            Evaluation dictionary with outcome and scores
        """
        # Get current state
        posture = simulator.get_security_posture()
        compromised_count = posture['compromised_hosts']
        total_hosts = posture['total_hosts']
        alert_count = posture['active_alerts']
        patches = posture['patched_services']
        
        # Build evaluation prompt
        system_prompt = "You are a cybersecurity exercise evaluator. Analyze the round objectively and determine outcomes."
        
        human_prompt = ORCHESTRATOR_PROMPT.format(
            round_number=round_num,
            red_action=f"{red_action.get('action', 'unknown')}: {red_action.get('reasoning', '')[:100]}",
            blue_action=f"{blue_action.get('action', 'unknown')}: {blue_action.get('reasoning', '')[:100]}",
            red_result=f"Success: {red_result.get('success', False)}, Details: {str(red_result)[:150]}",
            blue_result=f"Success: {blue_result.get('success', False)}, Details: {str(blue_result)[:150]}",
            compromised_count=compromised_count,
            total_hosts=total_hosts,
            alert_count=alert_count,
            patches=patches
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            evaluation = self._parse_evaluation(response.content)
        except Exception as e:
            logger.error(f"Orchestrator evaluation failed: {e}")
            evaluation = self._heuristic_evaluation(
                red_result, blue_result, compromised_count, 
                total_hosts, round_num
            )
        
        # Calculate scores based on actual game state
        red_points, blue_points = self._calculate_scores(
            simulator, red_result, blue_result, evaluation
        )
        
        evaluation["red_points"] = red_points
        evaluation["blue_points"] = blue_points
        
        # Determine if simulation should continue
        evaluation["continue_simulation"] = self._should_continue(
            simulator, round_num, compromised_count, total_hosts
        )
        
        # Store in history
        self.round_history.append({
            "round": round_num,
            "evaluation": evaluation,
            "state": {
                "compromised": compromised_count,
                "total": total_hosts,
                "alerts": alert_count
            }
        })
        
        logger.info(
            f"Round {round_num} evaluated: {evaluation['outcome']} | "
            f"Red +{red_points}, Blue +{blue_points}"
        )
        
        return evaluation
    
    def _parse_evaluation(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM evaluation response."""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                eval_data = json.loads(json_str)
                
                # Ensure required fields
                return {
                    "outcome": eval_data.get("outcome", "neutral"),
                    "red_points": eval_data.get("red_points", 0),
                    "blue_points": eval_data.get("blue_points", 0),
                    "continue_simulation": eval_data.get("continue_simulation", True),
                    "reasoning": eval_data.get("reasoning", "No reasoning provided"),
                    "key_observation": eval_data.get("key_observation", "")
                }
            else:
                raise ValueError("No JSON found")
        except Exception as e:
            logger.warning(f"Failed to parse orchestrator response: {e}")
            return {
                "outcome": "neutral",
                "red_points": 0,
                "blue_points": 0,
                "continue_simulation": True,
                "reasoning": "Parse error, using defaults",
                "key_observation": "Evaluation parsing failed"
            }
    
    def _heuristic_evaluation(self, red_result: Dict, blue_result: Dict,
                             compromised: int, total: int, 
                             round_num: int) -> Dict[str, Any]:
        """Fallback heuristic evaluation when LLM fails."""
        # Simple scoring based on results
        red_success = red_result.get("success", False)
        blue_success = blue_result.get("success", False)
        
        # Determine outcome
        if red_success and not blue_success:
            outcome = "red_success"
        elif blue_success and not red_success:
            outcome = "blue_success"
        elif red_success and blue_success:
            outcome = "neutral"  # Both succeeded
        else:
            outcome = "neutral"  # Both failed
        
        return {
            "outcome": outcome,
            "red_points": 0,  # Will be calculated separately
            "blue_points": 0,
            "continue_simulation": True,
            "reasoning": f"Heuristic: Red {'succeeded' if red_success else 'failed'}, "
                        f"Blue {'succeeded' if blue_success else 'failed'}",
            "key_observation": f"{compromised}/{total} hosts compromised"
        }
    
    def _calculate_scores(self, simulator, red_result: Dict, 
                         blue_result: Dict, evaluation: Dict) -> tuple[int, int]:
        """Calculate points for this round based on actions and state."""
        red_points = 0
        blue_points = 0
        
        # Red team scoring
        if red_result.get("success"):
            action_type = red_result.get("action_type", "")
            
            if red_result.get("host_compromised"):
                red_points += SCORING_WEIGHTS["host_compromised"]
            
            if red_result.get("persistence_established"):
                red_points += SCORING_WEIGHTS["persistence_established"]
            
            # Bonus for stealth (low detection score)
            detection_score = red_result.get("detection_score", 5)
            if detection_score < 3:
                red_points += 3  # Stealth bonus
            elif detection_score > 7:
                red_points -= 2  # Noisy penalty
        
        # Blue team scoring
        if blue_result.get("success"):
            action_type = blue_result.get("action_type", "")
            
            if "compromised_hosts_detected" in blue_result:
                detected = blue_result["compromised_hosts_detected"]
                if detected:
                    blue_points += SCORING_WEIGHTS["detection"] * -1  # Negative weight becomes positive
                    blue_points += len(detected) * 3
            
            if blue_result.get("service_patched"):
                blue_points += SCORING_WEIGHTS["successful_patch"] * -1
        
        # Check for false positives (blue team penalty)
        recent_alerts = [a for a in simulator.alerts[-5:] if a.false_positive]
        if recent_alerts:
            blue_points += SCORING_WEIGHTS["false_positive"] * len(recent_alerts)
        
        # Ensure points are non-negative
        red_points = max(0, red_points)
        blue_points = max(0, blue_points)
        
        return red_points, blue_points
    
    def _should_continue(self, simulator, round_num: int, 
                        compromised: int, total: int) -> bool:
        """Determine if simulation should continue."""
        # Max rounds reached
        if round_num >= MAX_ROUNDS:
            logger.info(f"Max rounds ({MAX_ROUNDS}) reached")
            return False
        
        # All hosts compromised - red team decisive victory
        if compromised >= total:
            logger.info("All hosts compromised - Red team victory")
            return False
        
        # All vulnerabilities patched and no compromises - blue team victory
        posture = simulator.get_security_posture()
        if (posture['patched_services'] == posture['total_services'] and 
            compromised == 0 and round_num >= 5):
            logger.info("All services patched with no compromises - Blue team victory")
            return False
        
        # Check for stalemate (no changes in last 3 rounds)
        if len(self.round_history) >= 3:
            recent = self.round_history[-3:]
            compromised_counts = [r["state"]["compromised"] for r in recent]
            if len(set(compromised_counts)) == 1 and compromised_counts[0] > 0:
                # Same number of compromised hosts for 3 rounds
                if round_num >= 8:  # Only end early if we've had enough rounds
                    logger.info("Stalemate detected - ending simulation")
                    return False
        
        return True
    
    def get_final_results(self, simulator) -> Dict[str, Any]:
        """Get final simulation results and determine winner."""
        posture = simulator.get_security_posture()
        red_total = sum(r["evaluation"]["red_points"] for r in self.round_history)
        blue_total = sum(r["evaluation"]["blue_points"] for r in self.round_history)
        
        # Determine winner
        if posture['compromised_hosts'] >= posture['total_hosts']:
            winner = "red"
            win_reason = "All hosts compromised"
        elif (posture['patched_services'] == posture['total_services'] and 
              posture['compromised_hosts'] == 0):
            winner = "blue"
            win_reason = "Complete defense - all patches applied, no compromises"
        elif red_total > blue_total:
            winner = "red"
            win_reason = f"Higher score ({red_total} vs {blue_total})"
        elif blue_total > red_total:
            winner = "blue"
            win_reason = f"Higher score ({blue_total} vs {red_total})"
        else:
            winner = "draw"
            win_reason = "Tied scores"
        
        return {
            "winner": winner,
            "win_reason": win_reason,
            "red_score": red_total,
            "blue_score": blue_total,
            "total_rounds": len(self.round_history),
            "final_state": {
                "compromised_hosts": posture['compromised_hosts'],
                "total_hosts": posture['total_hosts'],
                "patched_services": posture['patched_services'],
                "total_alerts": posture['active_alerts']
            },
            "key_observations": [
                r["evaluation"].get("key_observation", "")
                for r in self.round_history[-3:]
                if r["evaluation"].get("key_observation")
            ]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "rounds_evaluated": len(self.round_history),
            "model": self.model_name,
            "avg_red_points": sum(r["evaluation"]["red_points"] for r in self.round_history) / max(len(self.round_history), 1),
            "avg_blue_points": sum(r["evaluation"]["blue_points"] for r in self.round_history) / max(len(self.round_history), 1)
        }
