"""
src/agents/blue_team.py
Production-Grade Blue Team Agent.

Utilizes native LangChain tool-calling to respond dynamically to Red Team threats.
"""

import time
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from ..config import get_model_config, PERFORMANCE_CONFIG
from ..utils.prompts import BLUE_TEAM_SYSTEM_PROMPT
from ..utils.logger import setup_logger

# Import the actual tool functions to bind to the LLM
from .tools import detect_anomaly, patch_vulnerability, analyze_logs

logger = setup_logger("agents.blue")

class BlueTeamAgent:
    """
    Native Tool-Calling Defensive Agent.
    """
    def __init__(self, model_name: Optional[str] = None):
        config = get_model_config("blue")
        self.model_name = model_name or config["model"]
        
        # Initialize the defensive LLM (lower temperature for logical consistency)
        base_llm = ChatOllama(
            model=self.model_name,
            temperature=0.25,           
            top_p=0.85,
            num_ctx=PERFORMANCE_CONFIG["blue_team"]["num_ctx"],
            timeout=PERFORMANCE_CONFIG["blue_team"]["timeout"]
        )
        
        # Bind defensive tools natively
        self.tools = [detect_anomaly, patch_vulnerability, analyze_logs]
        self.bound_llm = base_llm.bind_tools(self.tools)
        
        logger.info(f"BlueTeamAgent initialized natively with tool-calling: {self.model_name}")

    def decide_action(self, state: Dict[str, Any], simulator) -> Any:
        """
        Reads the network state and ongoing message history to mount a defense.
        Returns an AIMessage for the ToolNode to execute.
        """
        posture = simulator.get_security_posture()
        recent_alerts = [a.description for a in simulator.alerts[-8:]]
        
        # Build the System Prompt
        system_content = BLUE_TEAM_SYSTEM_PROMPT.format(
            security_posture=str(posture),
            recent_alerts="\n".join(recent_alerts) if recent_alerts else "No recent alerts",
            attacker_activity="See message history for latest system events."
        )
        
        sys_msg = SystemMessage(content=system_content)
        
        # Combine system context with the graph's ongoing message history
        # This allows Blue to naturally "see" the Red Team's tool executions
        messages = [sys_msg] + state.get("messages", [])
        
        logger.info("Blue Team analyzing threat landscape...")
        
        try:
            # Invoke the bound LLM
            response = self.bound_llm.invoke(messages)
            return response
            
        except Exception as e:
            logger.error(f"BlueTeamAgent LLM failure: {e}", exc_info=True)
            from langchain_core.messages import AIMessage
            return AIMessage(content="Systems overloaded. Falling back to passive monitoring.")
