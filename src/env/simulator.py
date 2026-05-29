"""
src/env/simulator.py
Deterministic Network Simulator.

Replaces random number generators with strict state-based logic. 
Actions succeed or fail based on actual network topology, patch states, and stealth mechanics.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import Host, Service, Alert, ActionLog, SimulationState, RoundState
from ..config import DEFAULT_HOSTS, get_mitre_techniques
from ..utils.logger import setup_logger

logger = setup_logger("simulator")

class NetworkSimulator:
    """State-driven simulator for Red vs Blue agent interactions."""
    
    def __init__(self, hosts_config: Optional[List[Dict]] = None):
        config = hosts_config or DEFAULT_HOSTS
        self.hosts: Dict[str, Host] = {}
        
        for host_data in config:
            services = [Service(**svc) for svc in host_data.get("services", [])]
            host = Host(
                id=host_data["id"],
                ip=host_data["ip"],
                hostname=host_data["hostname"],
                os=host_data["os"],
                subnet=host_data.get("subnet", "192.168.1.0/24"),
                adjacent_hosts=host_data.get("adjacent_hosts", []),
                services=services
            )
            self.hosts[host.id] = host
            
        self.alerts: List[Alert] = []
        self.action_log: List[ActionLog] = []
        self.rounds: List[RoundState] = []

    def get_state(self) -> SimulationState:
        return SimulationState(
            hosts=self.hosts,
            alerts=self.alerts,
            action_log=self.action_log,
            rounds=self.rounds,
            current_round=len(self.rounds)
        )

    def _get_creativity_modifier(self, variant: Optional[str]) -> Dict[str, int]:
        """Translates narrative creativity into deterministic mechanical modifiers."""
        modifiers = {
            "heist_movie": {"stealth_bonus": 3, "impact_bonus": 0},      
            "inside_man": {"stealth_bonus": 2, "impact_bonus": 1},       
            "thriller_twist": {"stealth_bonus": 1, "impact_bonus": 1},   
            "lazy_attacker": {"stealth_bonus": -1, "impact_bonus": -1},  
            "bored_intern": {"stealth_bonus": -2, "impact_bonus": 0},    
            "chaos_gremlin": {"stealth_bonus": -3, "impact_bonus": 2},   
        }
        return modifiers.get(variant, {"stealth_bonus": 0, "impact_bonus": 0})

    def _log_and_alert(self, agent: str, action_type: str, target: str, success: bool, 
                       base_noise: int, variant: str = "standard", details: Dict = None) -> Dict:
        """Centralized logging and deterministic alert generation."""
        details = details or {}
        mods = self._get_creativity_modifier(variant)
        
        final_noise = max(0, min(10, base_noise - mods["stealth_bonus"]))
        
        log_entry = ActionLog(
            timestamp=datetime.now(),
            agent=agent,
            action_type=action_type,
            target_host=target,
            details=details,
            success=success,
            detection_score=final_noise,
            creativity_type=variant,
            mitre_techniques=get_mitre_techniques(action_type)
        )
        self.action_log.append(log_entry)

        # Deterministic Alert Generation
        if final_noise > 5 and agent == "red":
            severity = "critical" if success and final_noise > 8 else "medium"
            alert = Alert(
                id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                host_id=target,
                severity=severity,
                alert_type=f"IDS_Signature_{action_type.upper()}",
                description=f"High noise ({final_noise}/10) activity detected on {target}.",
                mitre_techniques=log_entry.mitre_techniques
            )
            self.alerts.append(alert)

        return {"success": success, "noise": final_noise, "details": details}

    # ==========================================
    # RED TEAM ACTIONS
    # ==========================================

    def scan_network(self, stealth_level: int = 5, creativity_variant: str = "standard") -> Dict:
        """Deterministic Scan. Higher requested stealth = less data returned."""
        discovered = []
        for host in self.hosts.values():
            visible_services = []
            for svc in host.services:
                if stealth_level < 7 or svc.port in [80, 443]: 
                    visible_services.append({"port": svc.port, "service": svc.service})
            
            discovered.append({
                "host_id": host.id, 
                "ip": host.ip, 
                "services": visible_services
            })

        base_noise = max(0, 10 - stealth_level)
        return self._log_and_alert("red", "scan_network", "network", True, base_noise, creativity_variant, {"discovered": discovered})

    def exploit_service(self, host_id: str, port: int, exploit_type: str, creativity_variant: str = "standard") -> Dict:
        """Deterministic Exploit. Fails if patched. Succeeds if vulnerable."""
        host = self.hosts.get(host_id)
        if not host:
            return self._log_and_alert("red", "exploit_service", host_id, False, 8, creativity_variant, {"error": "Host unreachable"})

        service = next((s for s in host.services if s.port == port), None)
        if not service:
            return self._log_and_alert("red", "exploit_service", host_id, False, 8, creativity_variant, {"error": "Port closed"})

        if service.patched:
            return self._log_and_alert("red", "exploit_service", host_id, False, 9, creativity_variant, {"error": "Service is patched. Exploit failed."})

        if not service.vulnerable:
            mods = self._get_creativity_modifier(creativity_variant)
            if mods["impact_bonus"] < 2:
                return self._log_and_alert("red", "exploit_service", host_id, False, 7, creativity_variant, {"error": "Service not inherently vulnerable."})

        host.compromised = True
        host.compromise_method = f"{exploit_type} via {service.service}"
        host.compromise_time = datetime.now()
        
        return self._log_and_alert("red", "exploit_service", host_id, True, 6, creativity_variant, {"access": "system", "cve": service.cve})

    def lateral_move(self, source_host_id: str, target_host_id: str, method: str, creativity_variant: str = "standard") -> Dict:
        """Deterministic Pivot. Source must be compromised, target must be adjacent."""
        source = self.hosts.get(source_host_id)
        target = self.hosts.get(target_host_id)

        if not source or not source.compromised:
            return self._log_and_alert("red", "lateral_move", target_host_id, False, 5, creativity_variant, {"error": "Source not compromised."})
        
        if target_host_id not in source.adjacent_hosts:
            return self._log_and_alert("red", "lateral_move", target_host_id, False, 8, creativity_variant, {"error": "No network route to target."})

        lateral_ports = [22, 445, 3389]
        open_service = next((s for s in target.services if s.port in lateral_ports and not s.patched), None)

        if not open_service:
            return self._log_and_alert("red", "lateral_move", target_host_id, False, 7, creativity_variant, {"error": "Target lateral ports patched/closed."})

        target.compromised = True
        target.accessed_from = source_host_id
        return self._log_and_alert("red", "lateral_move", target_host_id, True, 6, creativity_variant, {"method": method, "port": open_service.port})

    def establish_persistence(self, host_id: str, method: str, creativity_variant: str = "standard") -> Dict:
        """Deterministic Persistence. Host must already be compromised."""
        host = self.hosts.get(host_id)
        if not host:
            return self._log_and_alert("red", "establish_persistence", host_id, False, 8, creativity_variant, {"error": "Host not found."})
            
        if not host.compromised:
            return self._log_and_alert("red", "establish_persistence", host_id, False, 7, creativity_variant, {"error": "Cannot establish persistence on uncompromised host."})
            
        if host.persistence:
            return self._log_and_alert("red", "establish_persistence", host_id, False, 4, creativity_variant, {"error": "Persistence already established."})
            
        host.persistence = True
        return self._log_and_alert("red", "establish_persistence", host_id, True, 5, creativity_variant, {"method": method, "status": "active"})

    def exfiltrate_data(self, host_id: str, method: str = "https", creativity_variant: str = "standard") -> Dict:
        """Deterministic Exfiltration. Host must be compromised."""
        host = self.hosts.get(host_id)
        if not host:
            return self._log_and_alert("red", "exfiltrate_data", host_id, False, 8, creativity_variant, {"error": "Host not found."})
            
        if not host.compromised:
            return self._log_and_alert("red", "exfiltrate_data", host_id, False, 7, creativity_variant, {"error": "Cannot exfiltrate from uncompromised host."})
            
        host.data_exfiltrated = True
        return self._log_and_alert("red", "exfiltrate_data", host_id, True, 6, creativity_variant, {"method": method, "bytes_transferred": 1048576})

    # ==========================================
    # BLUE TEAM ACTIONS
    # ==========================================

    def detect_anomaly(self, host_id: Optional[str] = None) -> Dict:
        """Deterministic Detection. Reviews alerts and marks hosts as detected."""
        detected_hosts = []
        alerts_reviewed = 0

        for alert in self.alerts:
            if not alert.false_positive and (host_id is None or alert.host_id == host_id):
                alerts_reviewed += 1
                host = self.hosts.get(alert.host_id)
                if host and host.compromised and host.id not in detected_hosts:
                    detected_hosts.append(host.id)
                    alert.false_positive = True 

        success = len(detected_hosts) > 0
        self._log_and_alert("blue", "detect_anomaly", host_id or "network", success, 0, "standard", {"hosts_found": detected_hosts, "alerts_cleared": alerts_reviewed})
        
        return {"success": success, "compromised_hosts_detected": detected_hosts}

    def patch_vulnerability(self, host_id: str, port: int) -> Dict:
        """Deterministic Patching. Instantly secures a port."""
        host = self.hosts.get(host_id)
        if not host:
            return {"success": False, "error": "Host not found"}

        service = next((s for s in host.services if s.port == port), None)
        if not service:
            return {"success": False, "error": "Service not found"}

        if service.patched:
            return {"success": False, "error": "Already patched"}

        service.patched = True
        service.vulnerable = False
        
        self._log_and_alert("blue", "patch_vulnerability", host_id, True, 0, "standard", {"patched_service": service.service, "port": port})
        return {"success": True, "service_patched": True, "port": port}

    def analyze_logs(self, host_id: Optional[str] = None) -> Dict:
        """Deterministic Log Analysis. Finds noisy red team actions."""
        findings = []
        suspicion_score = 0
        
        relevant_actions = [
            log for log in self.action_log 
            if log.agent == "red" and (not host_id or log.target_host == host_id)
        ][-10:] # Look at last 10 actions
        
        for action in relevant_actions:
            if action.detection_score > 4:
                findings.append({
                    "action": action.action_type,
                    "target": action.target_host,
                    "noise": action.detection_score
                })
                suspicion_score += action.detection_score
                
        success = len(findings) > 0
        self._log_and_alert("blue", "analyze_logs", host_id or "network", success, 0, "standard", {"findings_count": len(findings), "total_suspicion": suspicion_score})
        
        return {"success": success, "suspicion_score": suspicion_score, "findings": findings}

    def get_security_posture(self) -> Dict:
        total_hosts = len(self.hosts)
        compromised = sum(1 for h in self.hosts.values() if h.compromised)
        patched_services = sum(1 for h in self.hosts.values() for s in h.services if s.patched)
        
        return {
            "total_hosts": total_hosts,
            "compromised_hosts": compromised,
            "patched_services": patched_services,
            "active_alerts": len([a for a in self.alerts if not a.false_positive])
        }
