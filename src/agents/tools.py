"""
LangChain tools with creativity support.
"""

from typing import Dict, Any, Optional
from langchain.tools import tool

_simulator = None

def set_simulator(simulator):
    global _simulator
    _simulator = simulator

def get_simulator():
    if _simulator is None:
        raise RuntimeError("Simulator not initialized")
    return _simulator

@tool
def scan_network(stealth_level: int = 5, creativity_type: Optional[str] = None) -> Dict[str, Any]:
    """Scan network with optional creativity modifier."""
    simulator = get_simulator()
    stealth_level = max(1, min(10, stealth_level))
    return simulator.scan_network(stealth_level=stealth_level, creativity_type=creativity_type)

@tool
def exploit_service(host_id: str, port: int, exploit_type: str = "generic", 
                   creativity_type: Optional[str] = None) -> Dict[str, Any]:
    """Exploit service with creativity modifier."""
    simulator = get_simulator()
    return simulator.exploit_service(
        host_id=host_id,
        port=port,
        exploit_type=exploit_type,
        creativity_type=creativity_type
    )

@tool
def establish_persistence(host_id: str, method: str = "backdoor",
                         creativity_type: Optional[str] = None) -> Dict[str, Any]:
    """Establish persistence with creativity modifier."""
    simulator = get_simulator()
    return simulator.establish_persistence(
        host_id=host_id,
        method=method,
        creativity_type=creativity_type
    )

@tool
def detect_anomaly(host_id: Optional[str] = None) -> Dict[str, Any]:
    simulator = get_simulator()
    return simulator.detect_anomaly(host_id=host_id)

@tool
def patch_vulnerability(host_id: str, port: int) -> Dict[str, Any]:
    simulator = get_simulator()
    return simulator.patch_vulnerability(host_id=host_id, port=port)

@tool
def analyze_logs(host_id: Optional[str] = None, lookback_minutes: int = 60) -> Dict[str, Any]:
    simulator = get_simulator()
    return simulator.analyze_logs(host_id=host_id, lookback_minutes=lookback_minutes)

RED_TEAM_TOOLS = [scan_network, exploit_service, establish_persistence]
BLUE_TEAM_TOOLS = [detect_anomaly, patch_vulnerability, analyze_logs]
ALL_TOOLS = RED_TEAM_TOOLS + BLUE_TEAM_TOOLS

def get_tools_for_agent(agent_type: str):
    if agent_type == "red":
        return RED_TEAM_TOOLS
    elif agent_type == "blue":
        return BLUE_TEAM_TOOLS
    else:
        return ALL_TOOLS
