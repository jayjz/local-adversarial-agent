"""
src/env/models.py
Pydantic data models for the simulation state.
Clean, validated, and serializable for exports/annotation.
"""

from typing import Dict, List, Optional, Literal, Annotated
from datetime import datetime
from pydantic import BaseModel, Field


class Service(BaseModel):
    port: int
    service: str
    version: str
    vulnerable: bool = False
    cve: Optional[str] = None
    creds: Optional[str] = None
    patched: bool = False
    mitre_techniques: List[str] = Field(default_factory=list)


class Host(BaseModel):
    id: str
    ip: str
    hostname: str
    os: str
    subnet: str = "192.168.1.0/24"
    adjacent_hosts: List[str] = Field(default_factory=list)
    services: List[Service]
    
    compromised: bool = False
    compromise_method: Optional[str] = None
    compromise_time: Optional[datetime] = None
    persistence: bool = False
    data_exfiltrated: bool = False
    accessed_from: Optional[str] = None


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=datetime.now)
    host_id: str
    severity: Literal["low", "medium", "high", "critical"]
    alert_type: str
    description: str
    source_ip: Optional[str] = None
    false_positive: bool = False
    mitre_techniques: List[str] = Field(default_factory=list)


class ActionLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    agent: Literal["red", "blue", "orchestrator", "human"]
    action_type: str
    target_host: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    detection_score: int = Field(ge=0, le=10, default=0)
    creativity_type: Optional[str] = None
    mitre_techniques: List[str] = Field(default_factory=list)


class SimulationState(BaseModel):
    hosts: Dict[str, Host]
    alerts: List[Alert] = Field(default_factory=list)
    action_log: List[ActionLog] = Field(default_factory=list)
    rounds: List[Dict] = Field(default_factory=list)
    current_round: int = 0
    red_score: int = 0
    blue_score: int = 0
