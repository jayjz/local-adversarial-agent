"""
Tests for agent implementations.
Tests focus on agent initialization and basic decision-making.
Note: Full LLM tests require Ollama to be running.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.red_team import RedTeamAgent
from src.agents.blue_team import BlueTeamAgent
from src.agents.orchestrator import OrchestratorAgent
from src.env.simulator import NetworkSimulator


@pytest.fixture
def simulator():
    """Create a fresh simulator for testing."""
    return NetworkSimulator()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with valid JSON."""
    mock_response = Mock()
    mock_response.content = '''
    {
        "reasoning": "Test reasoning",
        "action": "scan_network",
        "parameters": {"stealth_level": 5},
        "creativity_note": "Test creativity"
    }
    '''
    return mock_response


class TestRedTeamAgent:
    """Test Red Team agent functionality."""
    
    def test_initialization(self):
        """Test agent initializes correctly."""
        with patch('src.agents.red_team.ChatOllama'):
            agent = RedTeamAgent(model_name="test-model")
            assert agent.model_name == "test-model"
            assert agent.attack_history == []
    
    def test_fallback_decision_no_compromise(self, simulator):
        """Test fallback decision when no hosts compromised."""
        with patch('src.agents.red_team.ChatOllama'):
            agent = RedTeamAgent()
            decision = agent._fallback_decision(simulator, 1)
            
            assert "action" in decision
            assert "reasoning" in decision
            assert decision["action"] in ["scan_network", "exploit_service", "establish_persistence"]
    
    def test_validate_scan_decision(self, simulator):
        """Test decision validation for scan action."""
        with patch('src.agents.red_team.ChatOllama'):
            agent = RedTeamAgent()
            
            decision = {
                "action": "scan_network",
                "parameters": {}
            }
            
            validated = agent._validate_decision(decision, simulator)
            assert "stealth_level" in validated["parameters"]
            assert 1 <= validated["parameters"]["stealth_level"] <= 10
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        with patch('src.agents.red_team.ChatOllama'):
            agent = RedTeamAgent()
            
            response = '{"action": "test", "parameters": {}}'
            result = agent._parse_response(response)
            
            assert result["action"] == "test"
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON falls back gracefully."""
        with patch('src.agents.red_team.ChatOllama'):
            agent = RedTeamAgent()
            
            response = "This is not JSON at all"
            result = agent._parse_response(response)
            
            assert "action" in result
            assert result["action"] == "scan_network"  # Default fallback


class TestBlueTeamAgent:
    """Test Blue Team agent functionality."""
    
    def test_initialization(self):
        """Test agent initializes correctly."""
        with patch('src.agents.blue_team.ChatOllama'):
            agent = BlueTeamAgent(model_name="test-model")
            assert agent.model_name == "test-model"
            assert agent.defense_history == []
    
    def test_fallback_decision_with_alerts(self, simulator):
        """Test fallback decision when alerts exist."""
        with patch('src.agents.blue_team.ChatOllama'):
            agent = BlueTeamAgent()
            
            # Add a fake alert
            simulator._generate_alert(
                host_id="web-01",
                severity="high",
                alert_type="test",
                description="Test alert"
            )
            
            decision = agent._fallback_decision(simulator, 1)
            
            assert "action" in decision
            assert "confidence" in decision
            assert decision["action"] in ["detect_anomaly", "patch_vulnerability", "analyze_logs"]
    
    def test_validate_patch_decision(self, simulator):
        """Test decision validation for patch action."""
        with patch('src.agents.blue_team.ChatOllama'):
            agent = BlueTeamAgent()
            
            decision = {
                "action": "patch_vulnerability",
                "parameters": {}
            }
            
            validated = agent._validate_decision(decision, simulator)
            # Should auto-fill with a vulnerable service
            assert "host_id" in validated["parameters"] or validated["action"] != "patch_vulnerability"
    
    def test_assess_threat_level(self, simulator):
        """Test threat level assessment."""
        with patch('src.agents.blue_team.ChatOllama'):
            agent = BlueTeamAgent()
            
            # Initially should be LOW
            level = agent._assess_threat_level(simulator)
            assert level == "LOW"
            
            # Add alerts to increase threat
            for i in range(5):
                simulator._generate_alert(
                    host_id="web-01",
                    severity="medium",
                    alert_type="test",
                    description=f"Test {i}"
                )
            
            level = agent._assess_threat_level(simulator)
            assert level in ["HIGH", "CRITICAL"]


class TestOrchestratorAgent:
    """Test Orchestrator agent functionality."""
    
    def test_initialization(self):
        """Test orchestrator initializes correctly."""
        with patch('src.agents.orchestrator.ChatOllama'):
            orchestrator = OrchestratorAgent(model_name="test-model")
            assert orchestrator.model_name == "test-model"
            assert orchestrator.round_history == []
    
    def test_heuristic_evaluation(self, simulator):
        """Test heuristic evaluation fallback."""
        with patch('src.agents.orchestrator.ChatOllama'):
            orchestrator = OrchestratorAgent()
            
            red_result = {"success": True, "action_type": "exploit"}
            blue_result = {"success": False, "action_type": "detect"}
            
            evaluation = orchestrator._heuristic_evaluation(
                red_result, blue_result, 
                compromised=1, total=4, round_num=1
            )
            
            assert "outcome" in evaluation
            assert "reasoning" in evaluation
            assert evaluation["outcome"] == "red_success"
    
    def test_calculate_scores(self, simulator):
        """Test score calculation."""
        with patch('src.agents.orchestrator.ChatOllama'):
            orchestrator = OrchestratorAgent()
            
            red_result = {
                "success": True,
                "host_compromised": True,
                "detection_score": 2
            }
            blue_result = {
                "success": True,
                "service_patched": True
            }
            
            red_points, blue_points = orchestrator._calculate_scores(
                simulator, red_result, blue_result, {}
            )
            
            assert red_points > 0  # Should get points for compromise + stealth bonus
            assert blue_points > 0  # Should get points for patching
    
    def test_should_continue_max_rounds(self, simulator):
        """Test simulation stops at max rounds."""
        with patch('src.agents.orchestrator.ChatOllama'):
            orchestrator = OrchestratorAgent()
            
            # Should continue before max
            assert orchestrator._should_continue(simulator, 5, 1, 4) is True
            
            # Should stop at max (default 15)
            assert orchestrator._should_continue(simulator, 15, 1, 4) is False
    
    def test_should_continue_all_compromised(self, simulator):
        """Test simulation stops when all hosts compromised."""
        with patch('src.agents.orchestrator.ChatOllama'):
            orchestrator = OrchestratorAgent()
            
            # All hosts compromised should stop simulation
            assert orchestrator._should_continue(simulator, 5, 4, 4) is False
    
    def test_get_final_results(self, simulator):
        """Test final results calculation."""
        with patch('src.agents.orchestrator.ChatOllama'):
            orchestrator = OrchestratorAgent()
            
            # Add some mock history
            orchestrator.round_history = [
                {"evaluation": {"red_points": 10, "blue_points": 5, "key_observation": "Test 1"}},
                {"evaluation": {"red_points": 5, "blue_points": 10, "key_observation": "Test 2"}}
            ]
            
            results = orchestrator.get_final_results(simulator)
            
            assert "winner" in results
            assert "red_score" in results
            assert "blue_score" in results
            assert results["red_score"] == 15
            assert results["blue_score"] == 15


class TestAgentIntegration:
    """Integration tests for agents working together."""
    
    def test_agents_can_be_created(self):
        """Test that all agents can be instantiated."""
        with patch('src.agents.red_team.ChatOllama'), \
             patch('src.agents.blue_team.ChatOllama'), \
             patch('src.agents.orchestrator.ChatOllama'):
            
            red = RedTeamAgent()
            blue = BlueTeamAgent()
            orch = OrchestratorAgent()
            
            assert red is not None
            assert blue is not None
            assert orch is not None
    
    def test_agents_have_stats_methods(self):
        """Test that agents provide stats."""
        with patch('src.agents.red_team.ChatOllama'), \
             patch('src.agents.blue_team.ChatOllama'), \
             patch('src.agents.orchestrator.ChatOllama'):
            
            red = RedTeamAgent()
            blue = BlueTeamAgent()
            orch = OrchestratorAgent()
            
            red_stats = red.get_stats()
            blue_stats = blue.get_stats()
            orch_stats = orch.get_stats()
            
            assert "total_decisions" in red_stats
            assert "total_decisions" in blue_stats
            assert "rounds_evaluated" in orch_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
