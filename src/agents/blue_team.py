"""
Blue Team Agent - Defender
Uses Ollama with LangChain to make defensive decisions.
Methodical, alert-driven, learns from attacker behavior.
"""

import json
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import get_model_config, OLLAMA_BASE_URL
from ..utils.prompts import BLUE_TEAM_SYSTEM_PROMPT
from ..utils.logger import setup_logger

logger = setup_logger("agents.blue")


class BlueTeamAgent:
    """Defensive blue team agent focused on detection and response."""
    
    def __init__(self, model_name: str = None):
        """Initialize Blue Team agent with Ollama model."""
        config = get_model_config("blue")
        self.model_name = model_name or config["model"]
        
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=config["temperature"],
            top_p=config["top_p"],
            num_ctx=config["num_ctx"],
        )
        
        self.defense_history = []
        self.detection_patterns = {}
        logger.info(f"Blue Team initialized with model: {self.model_name}")
    
    def decide_action(self, simulator, round_num: int,
                     human_input: str = None) -> Dict[str, Any]:
        """
        Make a defensive decision based on current threats.
        
        Args:
            simulator: NetworkSimulator instance
            round_num: Current round number
            human_input: Optional human guidance
        
        Returns:
            Decision dictionary with action and parameters
        """
        # Build context
        security_posture = simulator.get_security_posture()
        recent_alerts = self._format_recent_alerts(simulator)
        attacker_activity = self._format_attacker_activity(simulator)
        
        # Build system prompt
        system_content = BLUE_TEAM_SYSTEM_PROMPT.format(
            security_posture=self._format_posture(security_posture),
            recent_alerts=recent_alerts,
            attacker_activity=attacker_activity
        )
        
        # Build human message
        human_content = f"""Round {round_num} - Defensive action required.

Current Threat Level: {self._assess_threat_level(simulator)}

Alerts requiring attention:
{recent_alerts}

Your recent defensive actions:
{self._get_recent_defenses(simulator)}

Choose your next defensive action. Prioritize:
1. Detecting active compromises
2. Patching critical vulnerabilities
3. Analyzing logs for attacker patterns

Respond ONLY with valid JSON:
{{
  "reasoning": "Your analysis of threats and priorities...",
  "action": "detect_anomaly|patch_vulnerability|analyze_logs",
  "parameters": {{"param": "value"}},
  "confidence": 7,
  "next_steps": "What you'll do after this action..."
}}
"""
        
        if human_input:
            human_content += f"\n\nHUMAN ANALYST NOTE: {human_input}\n"
            human_content += "Consider this insight in your defense strategy."
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=human_content)
        ]
        
        try:
            response = self.llm.invoke(messages)
            response_text = response.content
            
            decision = self._parse_response(response_text)
            decision = self._validate_decision(decision, simulator)
            
            self.defense_history.append({
                "round": round_num,
                "decision": decision,
                "threat_level": self._assess_threat_level(simulator),
                "human_guided": bool(human_input)
            })
            
            logger.info(f"Blue Team decision: {decision['action']} (confidence: {decision.get('confidence', 'N/A')})")
            
            return decision
            
        except Exception as e:
            logger.error(f"Blue Team decision failed: {e}")
            return self._fallback_decision(simulator, round_num)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON decision."""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                decision = json.loads(json_str)
                
                # Ensure required fields with defaults
                decision.setdefault("reasoning", "No reasoning provided")
                decision.setdefault("action", "detect_anomaly")
                decision.setdefault("parameters", {})
                decision.setdefault("confidence", 5)
                decision.setdefault("next_steps", "Continue monitoring")
                
                return decision
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse blue team response: {e}")
            return {
                "reasoning": "Parse error, defaulting to anomaly detection",
                "action": "detect_anomaly",
                "parameters": {},
                "confidence": 3,
                "next_steps": "Review system logs"
            }
    
    def _validate_decision(self, decision: Dict[str, Any], 
                          simulator) -> Dict[str, Any]:
        """Validate decision parameters against current state."""
        action = decision["action"]
        params = decision["parameters"]
        
        if action == "detect_anomaly":
            # Optional host_id parameter
            if "host_id" in params and params["host_id"]:
                if params["host_id"] not in simulator.hosts:
                    del params["host_id"]  # Remove invalid host_id
        
        elif action == "patch_vulnerability":
            # Need valid host_id and port
            if "host_id" not in params or "port" not in params:
                # Find most critical unpatched vulnerability
                for host in simulator.hosts.values():
                    for svc in host.services:
                        if svc.vulnerable and not svc.patched:
                            params["host_id"] = host.id
                            params["port"] = svc.port
                            break
                    if "host_id" in params:
                        break
                
                # If no vulnerabilities found, switch to detection
                if "host_id" not in params:
                    decision["action"] = "detect_anomaly"
                    decision["parameters"] = {}
            
            # Validate the host and port exist
            elif params["host_id"] in simulator.hosts:
                host = simulator.hosts[params["host_id"]]
                if not any(s.port == params["port"] for s in host.services):
                    # Invalid port, find a valid vulnerable service
                    for svc in host.services:
                        if svc.vulnerable and not svc.patched:
                            params["port"] = svc.port
                            break
        
        elif action == "analyze_logs":
            # Optional parameters with defaults
            params.setdefault("lookback_minutes", 60)
            if "host_id" in params and params["host_id"]:
                if params["host_id"] not in simulator.hosts:
                    del params["host_id"]
        
        return decision
    
    def _fallback_decision(self, simulator, round_num: int) -> Dict[str, Any]:
        """Heuristic fallback when LLM fails."""
        # Check for active alerts
        recent_alerts = [a for a in simulator.alerts[-5:] if not a.false_positive]
        
        if recent_alerts:
            # Have alerts, investigate them
            high_alerts = [a for a in recent_alerts if a.severity in ["high", "critical"]]
            if high_alerts:
                return {
                    "reasoning": "Fallback: High severity alerts detected, investigating",
                    "action": "detect_anomaly",
                    "parameters": {"host_id": high_alerts[0].host_id},
                    "confidence": 8,
                    "next_steps": "Patch vulnerabilities on affected hosts"
                }
        
        # Check for unpatched vulnerabilities
        for host in simulator.hosts.values():
            for svc in host.services:
                if svc.vulnerable and not svc.patched:
                    return {
                        "reasoning": "Fallback: Patching known vulnerability",
                        "action": "patch_vulnerability",
                        "parameters": {"host_id": host.id, "port": svc.port},
                        "confidence": 9,
                        "next_steps": "Continue monitoring for exploitation attempts"
                    }
        
        # Default: analyze logs
        return {
            "reasoning": "Fallback: No immediate threats, analyzing logs",
            "action": "analyze_logs",
            "parameters": {"lookback_minutes": 120},
            "confidence": 5,
            "next_steps": "Review findings and adjust defenses"
        }
    
    def _format_posture(self, posture: Dict) -> str:
        """Format security posture for prompt."""
        return f"""
- Hosts: {posture['healthy_hosts']}/{posture['total_hosts']} healthy ({posture['compromise_percentage']}% compromised)
- Services: {posture['patched_services']}/{posture['total_services']} patched
- Active Alerts: {posture['active_alerts']}
- Total Actions Logged: {posture['total_actions']}
"""
    
    def _format_recent_alerts(self, simulator, limit: int = 5) -> str:
        """Format recent alerts for context."""
        if not simulator.alerts:
            return "No alerts generated yet"
        
        recent = simulator.alerts[-limit:]
        formatted = []
        
        for alert in recent:
            formatted.append(
                f"[{alert.severity.upper()}] {alert.alert_type} on {alert.host_id}: "
                f"{alert.description}"
            )
        
        return "\n".join(formatted) if formatted else "No recent alerts"
    
    def _format_attacker_activity(self, simulator, limit: int = 5) -> str:
        """Format recent attacker activity from logs."""
        red_actions = [
            a for a in simulator.action_log[-20:]
            if a.agent == "red"
        ]
        
        if not red_actions:
            return "No attacker activity detected"
        
        recent = red_actions[-limit:]
        formatted = []
        
        for action in recent:
            status = "✓" if action.success else "✗"
            formatted.append(
                f"[{action.timestamp.strftime('%H:%M')}] {action.action_type} "
                f"on {action.target_host or 'network'} {status} "
                f"(noise level: {action.detection_score}/10)"
            )
        
        return "\n".join(formatted)
    
    def _get_recent_defenses(self, simulator, limit: int = 3) -> str:
        """Get summary of recent blue team actions."""
        blue_actions = [
            a for a in simulator.action_log[-10:]
            if a.agent == "blue"
        ]
        
        if not blue_actions:
            return "No defensive actions taken yet"
        
        recent = blue_actions[-limit:]
        return "\n".join([
            f"- {a.action_type} on {a.target_host or 'network'}"
            for a in recent
        ])
    
    def _assess_threat_level(self, simulator) -> str:
        """Assess current threat level."""
        posture = simulator.get_security_posture()
        recent_alerts = len([a for a in simulator.alerts[-10:] if not a.false_positive])
        
        if posture['compromised_hosts'] >= 2 or recent_alerts >= 5:
            return "CRITICAL"
        elif posture['compromised_hosts'] >= 1 or recent_alerts >= 3:
            return "HIGH"
        elif recent_alerts >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "total_decisions": len(self.defense_history),
            "human_guided_decisions": sum(1 for h in self.defense_history if h["human_guided"]),
            "model": self.model_name,
            "avg_confidence": sum(h["decision"].get("confidence", 5) for h in self.defense_history) / max(len(self.defense_history), 1)
        }
