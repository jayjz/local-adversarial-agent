"""
src/agents/tools.py
LangChain-compatible tool wrappers.

These are natively bound to the Red and Blue agents via .bind_tools().
"""

from typing import Dict, Any, Optional
from langchain.tools import tool
from ..env.simulator import NetworkSimulator

# Global simulator reference (set by workflow)
# Note: For a true parallel multi-tenant environment, this global state should be 
# refactored using InjectedToolArg, but for a local PoC, this singleton is acceptable.
_simulator: Optional[NetworkSimulator] = None

def set_simulator(simulator: NetworkSimulator):
    global _simulator
    _simulator = simulator

def get_simulator() -> NetworkSimulator:
    if _simulator is None:
        raise RuntimeError("Simulator not initialized. Call set_simulator() first.")
    return _simulator

# ==========================================
# RED TEAM TOOLS
# ==========================================

@tool
def scan_network(stealth_level: int = 5, creativity_variant: str = "standard") -> Dict[str, Any]:
    """Scan the network to discover hosts and open services."""
    return get_simulator().scan_network(stealth_level, creativity_variant)

@tool
def exploit_service(host_id: str, port: int, exploit_type: str = "generic", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Attempt to exploit a vulnerable service on a target host to gain access."""
    return get_simulator().exploit_service(host_id, port, exploit_type, creativity_variant)

@tool
def establish_persistence(host_id: str, method: str = "backdoor", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Establish persistence on a host that has already been compromised."""
    return get_simulator().establish_persistence(host_id, method, creativity_variant)

@tool
def lateral_move(source_host_id: str, target_host_id: str, method: str = "ssh", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Pivot from a compromised source host to an adjacent target host."""
    return get_simulator().lateral_move(source_host_id, target_host_id, method, creativity_variant)

@tool
def exfiltrate_data(host_id: str, method: str = "https", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Exfiltrate sensitive data from a compromised host."""
    return get_simulator().exfiltrate_data(host_id, method, creativity_variant)

# ==========================================
# BLUE TEAM TOOLS
# ==========================================

@tool
def detect_anomaly(host_id: Optional[str] = None) -> Dict[str, Any]:
    """Review SIEM alerts to detect compromised hosts."""
    return get_simulator().detect_anomaly(host_id)

@tool
def patch_vulnerability(host_id: str, port: int) -> Dict[str, Any]:
    """Secure a host by patching a specific vulnerable port."""
    return get_simulator().patch_vulnerability(host_id, port)

@tool
def analyze_logs(host_id: Optional[str] = None) -> Dict[str, Any]:
    """Analyze system logs to find noisy or suspicious actions."""
    return get_simulator().analyze_logs(host_id)
