"""
src/agents/blue_team.py
Production-Grade Blue Team Agent.

Utilizes native LangChain tool-calling to respond dynamically to Red Team threats.
"""

from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from ..config import get_model_config, PERFORMANCE_CONFIG
from ..utils.prompts import BLUE_TEAM_SYSTEM_PROMPT
from ..utils.logger import setup_logger

from .tools import detect_anomaly, patch_vulnerability, analyze_logs

logger = setup_logger("agents.blue")

class BlueTeamAgent:
    """Native Tool-Calling Defensive Agent."""
    
    def __init__(self, model_name: Optional[str] = None):
        config = get_model_config("blue")
        self.model_name = model_name or config["model"]
        
        base_llm = ChatOllama(
            model=self.model_name,
            temperature=0.20,           
            top_p=0.85,
            num_ctx=PERFORMANCE_CONFIG["blue_team"]["num_ctx"],
            timeout=PERFORMANCE_CONFIG["blue_team"]["timeout"]
        )
        
        self.tools = [detect_anomaly, patch_vulnerability, analyze_logs]
        self.bound_llm = base_llm.bind_tools(self.tools)
        
        logger.info(f"BlueTeamAgent initialized natively with tool-calling: {self.model_name}")

    def decide_action(self, state: Dict[str, Any], simulator) -> Any:
        """Reads network state and message history to mount a defense."""
        posture = simulator.get_security_posture()
        active_alerts = [a.description for a in simulator.alerts if not a.false_positive][-5:]
        
        system_content = BLUE_TEAM_SYSTEM_PROMPT.format(
            security_posture=str(posture),
            recent_alerts="\n".join(active_alerts) if active_alerts else "Network is quiet. No active alerts."
        )
        
        system_content += "\n\nCRITICAL DIRECTIVE: Analyze the message history below to observe the Red Team's tool outputs. Call the appropriate defensive tool (detect_anomaly, patch_vulnerability, analyze_logs) to neutralize the threat."
        
        sys_msg = SystemMessage(content=system_content)
        messages = [sys_msg] + state.get("messages", [])
        
        logger.info("Blue Team analyzing threat landscape...")
        
        try:
            return self.bound_llm.invoke(messages)
        except Exception as e:
            logger.error(f"BlueTeamAgent LLM failure: {e}", exc_info=True)
            from langchain_core.messages import AIMessage
            return AIMessage(content="SIEM systems overloaded. Passing turn to maintain uptime.")
