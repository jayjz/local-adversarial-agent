"""
Configuration for Local Adversarial Arena.
Centralized settings for models, simulation parameters, and Ollama connection.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# Model Configuration
# Use llama3.2 as default, but allow override via env vars
RED_TEAM_MODEL = os.getenv("RED_TEAM_MODEL", "llama3.2:latest")
BLUE_TEAM_MODEL = os.getenv("BLUE_TEAM_MODEL", "llama3.2:latest")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "llama3.2:3b")

# Simulation Settings
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "15"))
MAX_TURNS_PER_ROUND = int(os.getenv("MAX_TURNS_PER_ROUND", "3"))

# Human-in-the-Loop
ENABLE_HUMAN_INTERVENTION = os.getenv("ENABLE_HUMAN_INTERVENTION", "true").lower() == "true"
HUMAN_TIMEOUT_SECONDS = int(os.getenv("HUMAN_TIMEOUT_SECONDS", "300"))  # 5 minutes

# Network Simulation
DEFAULT_HOSTS = [
    {
        "id": "web-01",
        "ip": "192.168.1.10",
        "hostname": "web-server",
        "os": "Ubuntu 20.04",
        "services": [
            {"port": 80, "service": "http", "version": "Apache 2.4.41", "vulnerable": True, "cve": "CVE-2021-41773"},
            {"port": 22, "service": "ssh", "version": "OpenSSH 8.2", "vulnerable": True, "creds": "admin:admin123"}
        ]
    },
    {
        "id": "db-01",
        "ip": "192.168.1.20",
        "hostname": "database",
        "os": "Ubuntu 22.04",
        "services": [
            {"port": 3306, "service": "mysql", "version": "MySQL 8.0", "vulnerable": True, "creds": "root:password"},
            {"port": 22, "service": "ssh", "version": "OpenSSH 8.9", "vulnerable": False}
        ]
    },
    {
        "id": "ws-01",
        "ip": "192.168.1.30",
        "hostname": "workstation-01",
        "os": "Windows 10",
        "services": [
            {"port": 445, "service": "smb", "version": "SMBv1", "vulnerable": True, "cve": "EternalBlue"},
            {"port": 3389, "service": "rdp", "version": "RDP", "vulnerable": True, "creds": "user:Password123"}
        ]
    },
    {
        "id": "app-01",
        "ip": "192.168.1.40",
        "hostname": "app-server",
        "os": "Ubuntu 20.04",
        "services": [
            {"port": 8080, "service": "http", "version": "Tomcat 9.0", "vulnerable": True, "cve": "CVE-2020-9484"},
            {"port": 22, "service": "ssh", "version": "OpenSSH 8.2", "vulnerable": False}
        ]
    }
]

# Scoring
SCORING_WEIGHTS = {
    "host_compromised": 10,
    "persistence_established": 15,
    "data_exfiltrated": 20,
    "detection": -5,  # Blue team gains points for detection
    "successful_patch": -10,
    "false_positive": -2
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Export/Annotation
EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")
DEFAULT_EXPORT_FORMAT = "json"  # json or csv

# Streamlit UI
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
STREAMLIT_THEME = {
    "primaryColor": "#FF4B4B",
    "backgroundColor": "#0E1117",
    "secondaryBackgroundColor": "#262730",
    "textColor": "#FAFAFA"
}

def get_model_config(agent_type: str) -> Dict[str, Any]:
    """Get model configuration for a specific agent type."""
    configs = {
        "red": {
            "model": RED_TEAM_MODEL,
            "temperature": 0.9,  # Higher for creativity
            "top_p": 0.95,
            "num_ctx": 4096,
        },
        "blue": {
            "model": BLUE_TEAM_MODEL,
            "temperature": 0.3,  # Lower for consistency
            "top_p": 0.9,
            "num_ctx": 4096,
        },
        "orchestrator": {
            "model": ORCHESTRATOR_MODEL,
            "temperature": 0.1,  # Very low for deterministic judging
            "top_p": 0.8,
            "num_ctx": 2048,
        }
    }
    return configs.get(agent_type, configs["red"])

def check_ollama_available() -> tuple[bool, str]:
    """Check if Ollama is accessible. Returns (available, message)."""
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return True, f"Ollama available with models: {', '.join(models[:3])}"
        return False, f"Ollama returned status {response.status_code}"
    except ImportError:
        return False, "requests library not available"
    except Exception as e:
        return False, f"Ollama not accessible at {OLLAMA_BASE_URL}: {str(e)}"

def validate_config() -> list[str]:
    """Validate configuration and return list of warnings/errors."""
    issues = []
    
    # Check Ollama
    available, msg = check_ollama_available()
    if not available:
        issues.append(f"WARNING: {msg}")
        issues.append("  → Start Ollama with: ollama serve")
        issues.append("  → Pull models with: ollama pull llama3.2:latest")
    
    # Check directories
    for dir_path in [LOG_DIR, EXPORT_DIR]:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                issues.append(f"WARNING: Could not create {dir_path}: {e}")
    
    return issues
