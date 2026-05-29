"""Blue Team agent with full implementation."""
import time
from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from ..config import get_model_config
from ..utils.prompts import BLUE_TEAM_SYSTEM_PROMPT
from ..utils.logger import setup_logger
from ..utils.json_parser import safe_parse_llm_response

logger = setup_logger("agents.blue")

class BlueTeamAgent:
    def __init__(self, model_name: str = None):
        config = get_model_config("blue")
        self.model_name = model_name or config["model"]
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=config["base_url"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            num_ctx=config["num_ctx"],
            timeout=config["timeout"]
        )
        self.history = []
        logger.info(f"Blue Team initialized: {self.model_name}")

    def decide_action(self, simulator, round_num: int, human_input: str = None) -> Dict[str, Any]:
        start_time = time.time()
        posture = simulator.get_security_posture()
        recent_alerts = [a.description for a in simulator.alerts[-8:]]
        recent_attacks = [log.action_type for log in simulator.action_log[-6:] if log.agent == "red"]
        
        system_content = BLUE_TEAM_SYSTEM_PROMPT.format(
            security_posture=str(posture),
            recent_alerts="\n".join(recent_alerts) if recent_alerts else "No recent alerts",
            attacker_activity="\n".join(recent_attacks) if recent_attacks else "No recent attacker activity"
        )
        
        human_content = f"""Round {round_num}. Respond with JSON:
{{
  "reasoning": "Your analysis",
  "action": "detect_anomaly|patch_vulnerability|analyze_logs",
  "parameters": {{}},
  "confidence": 5,
  "next_steps": "..."
}}"""
        
        if human_input:
            human_content += f"\n\nHUMAN: {human_input}"
        
        messages = [SystemMessage(content=system_content), HumanMessage(content=human_content)]
        
        try:
            response = self.llm.invoke(messages)
            decision = safe_parse_llm_response(response.content, default={
                "reasoning": "Default detection",
                "action": "detect_anomaly",
                "parameters": {},
                "confidence": 5,
                "next_steps": "Monitor"
            })
            
            decision["execution_time_ms"] = int((time.time() - start_time) * 1000)
            self.history.append(decision)
            logger.info(f"Blue: {decision['action']}")
            return decision
        except Exception as e:
            logger.error(f"Blue error: {e}")
            return {
                "reasoning": "Error fallback",
                "action": "detect_anomaly",
                "parameters": {},
                "confidence": 3,
                "next_steps": "Manual review required",
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
