"""
Red Team Agent with creativity tracking.
Passes prompt variant to simulator for mechanical effects.
"""

import json
import random
import time
from typing import Dict, Any, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import get_model_config, OLLAMA_BASE_URL, OLLAMA_RETRY_ATTEMPTS, OLLAMA_RETRY_DELAY, FALLBACK_MODELS
from ..utils.prompts import RED_TEAM_SYSTEM_PROMPT, get_red_prompt_variant, format_network_state, format_recent_actions, RED_TEAM_CREATIVE_VARIANTS
from ..utils.logger import setup_logger
from ..utils.json_parser import safe_parse_llm_response

logger = setup_logger("agents.red")

class RedTeamAgent:
    def __init__(self, model_name: str = None):
        config = get_model_config("red")
        self.model_name = model_name or config["model"]
        self.fallback_models = FALLBACK_MODELS.copy()
        self.llm = self._create_llm(self.model_name, config)
        self.attack_history = []
        self.creative_mode = True
        self.consecutive_failures = 0
        self.current_creativity_type = None
        logger.info(f"Red Team initialized with model: {self.model_name}")
    
    def _create_llm(self, model_name: str, config: Dict) -> ChatOllama:
        return ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=config["temperature"],
            top_p=config["top_p"],
            num_ctx=config["num_ctx"],
            timeout=config.get("timeout", 120),
        )
    
    def _invoke_with_retry(self, messages, max_retries: int = None):
        max_retries = max_retries or OLLAMA_RETRY_ATTEMPTS
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                self.consecutive_failures = 0
                return response
            except Exception as e:
                self.consecutive_failures += 1
                logger.warning(f"LLM invoke failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(OLLAMA_RETRY_DELAY * (attempt + 1))
                    if self.consecutive_failures >= 2 and self.fallback_models:
                        fallback = self.fallback_models.pop(0)
                        logger.info(f"Switching to fallback model: {fallback}")
                        config = get_model_config("red")
                        self.llm = self._create_llm(fallback, config)
                        self.model_name = fallback
                else:
                    raise
    
    def decide_action(self, simulator, round_num: int, human_input: str = None) -> Dict[str, Any]:
        """Make decision and track which creativity variant is active."""
        network_state = format_network_state(simulator)
        recent_actions = format_recent_actions(simulator)
        
        # Select and store creativity variant
        variant = random.choice(RED_TEAM_CREATIVE_VARIANTS)
        self.current_creativity_type = variant["name"]
        variant_prompt = variant["prompt"]
        
        system_content = RED_TEAM_SYSTEM_PROMPT.format(
            network_state=network_state,
            recent_actions=recent_actions
        ) + f"\n\nCREATIVE APPROACH ({self.current_creativity_type}):\n{variant_prompt}"
        
        posture = simulator.get_security_posture()
        human_content = f"""Round {round_num} - Attack using {self.current_creativity_type} approach.

Compromised: {posture['compromised_hosts']}/{posture['total_hosts']}, Alerts: {posture['active_alerts']}

Respond with JSON:
{{"reasoning": "...", "action": "scan_network|exploit_service|establish_persistence", "parameters": {{}}, "creativity_note": "..."}}"""
        
        if human_input:
            human_content += f"\n\nHUMAN: {human_input}"
        
        messages = [SystemMessage(content=system_content), HumanMessage(content=human_content)]
        
        try:
            if round_num == 1:
                logger.info(f"🤖 Red Team thinking with {self.current_creativity_type}...")
            
            response = self._invoke_with_retry(messages)
            decision = safe_parse_llm_response(
                response.content,
                default={
                    "reasoning": "Parse failed",
                    "action": "scan_network",
                    "parameters": {"stealth_level": 5},
                    "creativity_note": "Fallback"
                }
            )
            
            # Add creativity type to decision for simulator
            decision["creativity_type"] = self.current_creativity_type
            decision = self._validate_decision(decision, simulator)
            
            self.attack_history.append({
                "round": round_num,
                "decision": decision,
                "creativity_type": self.current_creativity_type,
                "human_guided": bool(human_input)
            })
            
            logger.info(f"✓ Red [{self.current_creativity_type}]: {decision['action']}")
            return decision
            
        except Exception as e:
            logger.error(f"Red Team failed: {e}")
            fallback = self._fallback_decision(simulator, round_num)
            fallback["creativity_type"] = "fallback"
            return fallback
    
    def _validate_decision(self, decision: Dict[str, Any], simulator) -> Dict[str, Any]:
        decision.setdefault("action", "scan_network")
        decision.setdefault("parameters", {})
        decision.setdefault("reasoning", "No reasoning")
        
        action = decision["action"]
        params = decision["parameters"]
        
        if action == "scan_network":
            params["stealth_level"] = max(1, min(10, params.get("stealth_level", 5)))
        elif action == "exploit_service":
            if "host_id" not in params or "port" not in params:
                vulnerable = [(h.id, s.port) for h in simulator.hosts.values() 
                             for s in h.services if s.vulnerable and not s.patched]
                if vulnerable:
                    params["host_id"], params["port"] = random.choice(vulnerable)
                else:
                    decision["action"] = "scan_network"
                    params = {"stealth_level": 5}
            params.setdefault("exploit_type", "generic")
        elif action == "establish_persistence":
            candidates = [h.id for h in simulator.hosts.values() 
                        if h.compromised and not h.persistence]
            if candidates and "host_id" not in params:
                params["host_id"] = random.choice(candidates)
            params.setdefault("method", "backdoor")
        
        decision["parameters"] = params
        return decision
    
    def _fallback_decision(self, simulator, round_num: int) -> Dict[str, Any]:
        vulnerable = [(h.id, s.port) for h in simulator.hosts.values() 
                     for s in h.services if s.vulnerable and not s.patched and not h.compromised]
        
        if vulnerable:
            host_id, port = random.choice(vulnerable)
            return {
                "reasoning": "Fallback exploit",
                "action": "exploit_service",
                "parameters": {"host_id": host_id, "port": port, "exploit_type": "default_creds"},
                "creativity_note": "Auto",
                "creativity_type": "fallback"
            }
        
        return {
            "reasoning": "Fallback scan",
            "action": "scan_network",
            "parameters": {"stealth_level": 5},
            "creativity_note": "Auto",
            "creativity_type": "fallback"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        creativity_counts = {}
        for h in self.attack_history:
            ctype = h.get("creativity_type", "unknown")
            creativity_counts[ctype] = creativity_counts.get(ctype, 0) + 1
        
        return {
            "total_decisions": len(self.attack_history),
            "model": self.model_name,
            "creativity_distribution": creativity_counts,
            "failures": self.consecutive_failures
        }
