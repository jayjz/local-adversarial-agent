"""
src/agents/tools.py
LangChain-compatible tool wrappers.
These are bound to both Red and Blue agents.
"""

from typing import Dict, Any, Optional
from langchain.tools import tool

from ..env.simulator import NetworkSimulator

# Global simulator reference (set by workflow)
_simulator: Optional[NetworkSimulator] = None


def set_simulator(simulator: NetworkSimulator):
    global _simulator
    _simulator = simulator


def get_simulator() -> NetworkSimulator:
    if _simulator is None:
        raise RuntimeError("Simulator not initialized. Call set_simulator() first.")
    return _simulator


@tool
def scan_network(stealth_level: int = 5, creativity_variant: str = "standard") -> Dict[str, Any]:
    """Scan the network."""
    return get_simulator().scan_network(stealth_level, creativity_variant)


@tool
def exploit_service(host_id: str, port: int, exploit_type: str = "generic", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Exploit a service on a host."""
    return get_simulator().exploit_service(host_id, port, exploit_type, creativity_variant)


@tool
def establish_persistence(host_id: str, method: str = "backdoor", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Establish persistence on a compromised host."""
    # Add implementation in simulator if missing
    return {"success": False, "error": "Not implemented yet"}


@tool
def lateral_move(source_host_id: str, target_host_id: str, method: str = "ssh", creativity_variant: str = "standard") -> Dict[str, Any]:
    """Lateral movement from compromised host."""
    return get_simulator().lateral_move(source_host_id, target_host_id, method, creativity_variant)


@tool
def detect_anomaly(host_id: Optional[str] = None) -> Dict[str, Any]:
    """Blue Team detection."""
    return get_simulator().detect_anomaly(host_id)


@tool
def patch_vulnerability(host_id: str, port: int) -> Dict[str, Any]:
    """Blue Team patching."""
    return get_simulator().patch_vulnerability(host_id, port)
