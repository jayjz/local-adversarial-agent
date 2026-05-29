"""
src/agents/red_team.py
Production-Grade Red Team Agent.

Utilizes native LangChain tool-calling (.bind_tools) for deterministic execution.
"""

import time
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from ..config import get_model_config, PERFORMANCE_CONFIG
from ..utils.prompts import RED_TEAM_SYSTEM_PROMPT, get_red_prompt_variant, format_network_state
from ..utils.logger import setup_logger

from .tools import scan_network, exploit_service, establish_persistence, lateral_move, exfiltrate_data

logger = setup_logger("agents.red")

class RedTeamAgent:
    """Native Tool-Calling Red Team Agent."""
    
    def __init__(self, model_name: Optional[str] = None):
        config = get_model_config("red")
        self.model_name = model_name or config["model"]
        
        base_llm = ChatOllama(
            model=self.model_name,
            temperature=0.85,           
            top_p=0.92,
            num_ctx=PERFORMANCE_CONFIG["red_team"]["num_ctx"],
            timeout=PERFORMANCE_CONFIG["red_team"]["timeout"]
        )
        
        self.tools = [scan_network, exploit_service, establish_persistence, lateral_move, exfiltrate_data]
        self.bound_llm = base_llm.bind_tools(self.tools)
        
        logger.info(f"RedTeamAgent initialized natively with tool-calling: {self.model_name}")

    def _select_variant(self, round_number: int, posture: Dict) -> str:
        """Strategic variant selection based on real game state."""
        compromised = posture.get("compromised_hosts", 0)
        alerts = posture.get("active_alerts", 0)
        
        if round_number <= 2 or compromised == 0:
            return "heist_movie"
        elif alerts >= 5:
            return "chaos_gremlin"
        elif compromised >= 2:
            return "inside_man"
        elif alerts >= 2:
            return "thriller_twist"
        else:
            return "lazy_attacker"

    def decide_action(self, state: Dict[str, Any], simulator) -> Any:
        """Invokes the bound LLM. Returns an AIMessage for LangGraph."""
        round_num = state.get("round_number", 1)
        posture = simulator.get_security_posture()
        network_state = format_network_state(simulator)
        
        variant = self._select_variant(round_num, posture)
        variant_prompt = get_red_prompt_variant(variant)
        
        system_content = RED_TEAM_SYSTEM_PROMPT.format(
            network_state=network_state,
            recent_actions="See message history for recent tool outputs."
        )
        
        system_content += f"\n\nCURRENT DIRECTIVE:\nRound {round_num}. Alert Level: {posture.get('active_alerts', 0)}.\nExecute your turn using the '{variant}' style. {variant_prompt}"
        
        sys_msg = SystemMessage(content=system_content)
        messages = [sys_msg] + state.get("messages", [])
        
        logger.info(f"Red [{variant}] thinking...")
        
        try:
            return self.bound_llm.invoke(messages)
        except Exception as e:
            logger.error(f"RedTeamAgent LLM failure: {e}", exc_info=True)
            from langchain_core.messages import AIMessage
            return AIMessage(content="I am encountering cognitive errors. Passing turn.")
