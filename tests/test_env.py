"""
Tests for the network simulator environment.
"""

import pytest
from src.env.simulator import NetworkSimulator
from src.env.models import Host, Service


def test_simulator_initialization():
    """Test that simulator initializes with default hosts."""
    simulator = NetworkSimulator()
    
    assert len(simulator.hosts) == 4
    assert "web-01" in simulator.hosts
    assert "db-01" in simulator.hosts
    assert "ws-01" in simulator.hosts
    assert "app-01" in simulator.hosts


def test_host_structure():
    """Test that hosts have correct structure."""
    simulator = NetworkSimulator()
    web_host = simulator.hosts["web-01"]
    
    assert web_host.id == "web-01"
    assert web_host.ip == "192.168.1.10"
    assert len(web_host.services) == 2
    assert not web_host.compromised


def test_scan_network():
    """Test network scanning functionality."""
    simulator = NetworkSimulator()
    
    result = simulator.scan_network(stealth_level=5)
    
    assert result["success"] is True
    assert "discovered_hosts" in result
    assert len(result["discovered_hosts"]) == 4
    assert result["detection_score"] == 5  # 10 - stealth_level
    
    # Check that action was logged
    assert len(simulator.action_log) == 1
    assert simulator.action_log[0].action_type == "scan_network"


def test_exploit_vulnerable_service():
    """Test exploiting a vulnerable service."""
    simulator = NetworkSimulator()
    
    # Web server port 80 is vulnerable
    result = simulator.exploit_service("web-01", 80, "test_exploit")
    
    assert "success" in result
    assert "detection_score" in result
    
    # If successful, host should be marked compromised
    if result["success"]:
        assert simulator.hosts["web-01"].compromised is True
        assert simulator.hosts["web-01"].compromise_method is not None


def test_exploit_nonexistent_host():
    """Test exploiting non-existent host fails gracefully."""
    simulator = NetworkSimulator()
    
    result = simulator.exploit_service("nonexistent", 80)
    
    assert result["success"] is False
    assert "error" in result


def test_persistence_requires_compromise():
    """Test that persistence requires host to be compromised first."""
    simulator = NetworkSimulator()
    
    # Try to establish persistence on uncompromised host
    result = simulator.establish_persistence("web-01", "backdoor")
    
    assert result["success"] is False
    assert "not compromised" in result["error"].lower()


def test_patch_vulnerability():
    """Test patching a vulnerable service."""
    simulator = NetworkSimulator()
    
    # Patch the vulnerable web service
    result = simulator.patch_vulnerability("web-01", 80)
    
    assert result["success"] is True
    assert result["service_patched"] is True
    
    # Verify service is marked as patched
    web_host = simulator.hosts["web-01"]
    http_service = next(s for s in web_host.services if s.port == 80)
    assert http_service.patched is True
    assert http_service.vulnerable is False


def test_detect_anomaly():
    """Test anomaly detection."""
    simulator = NetworkSimulator()
    
    # Generate some activity first
    simulator.scan_network()
    simulator.exploit_service("web-01", 80)
    
    # Now detect
    result = simulator.detect_anomaly()
    
    assert result["success"] is True
    assert "alerts" in result
    assert "compromised_hosts_detected" in result


def test_analyze_logs():
    """Test log analysis."""
    simulator = NetworkSimulator()
    
    # Generate activity
    simulator.scan_network(stealth_level=3)  # Noisy scan
    simulator.exploit_service("web-01", 22)
    
    # Analyze logs
    result = simulator.analyze_logs(lookback_minutes=60)
    
    assert result["success"] is True
    assert "actions_analyzed" in result
    assert "suspicion_score" in result
    assert result["actions_analyzed"] > 0


def test_security_posture():
    """Test security posture reporting."""
    simulator = NetworkSimulator()
    
    posture = simulator.get_security_posture()
    
    assert "total_hosts" in posture
    assert "compromised_hosts" in posture
    assert "healthy_hosts" in posture
    assert "compromise_percentage" in posture
    assert posture["total_hosts"] == 4
    assert posture["compromised_hosts"] == 0
    assert posture["healthy_hosts"] == 4


def test_action_logging():
    """Test that actions are properly logged."""
    simulator = NetworkSimulator()
    
    initial_count = len(simulator.action_log)
    
    simulator.scan_network()
    simulator.exploit_service("web-01", 80)
    
    assert len(simulator.action_log) == initial_count + 2
    
    # Check log entries have required fields
    for log in simulator.action_log:
        assert log.timestamp is not None
        assert log.agent in ["red", "blue", "orchestrator", "human"]
        assert log.action_type is not None
        assert isinstance(log.success, bool)


def test_alert_generation():
    """Test that security alerts are generated."""
    simulator = NetworkSimulator()
    
    initial_alerts = len(simulator.alerts)
    
    # Perform noisy action that should generate alert
    simulator.scan_network(stealth_level=1)  # Very noisy
    
    # Should have generated at least one alert
    assert len(simulator.alerts) > initial_alerts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
