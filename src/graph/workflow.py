"""Complete LangGraph workflow with proper state management and tool binding."""
import time
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..config import get_model_config
from ..agents.red_team import RedTeamAgent
from ..agents.blue_team import BlueTeamAgent
from ..agents.orchestrator import OrchestratorAgent
from ..agents.tools import set_simulator
from ..env.simulator import NetworkSimulator
from ..env.models import GraphState
from ..utils.logger import setup_logger

logger = setup_logger("graph.workflow")


def create_workflow(red_model: str = None, blue_model: str = None, orchestrator_model: str = None, max_rounds: int = 8):
    """Create the complete LangGraph workflow."""
    simulator = NetworkSimulator()
    set_simulator(simulator)
    
    red_agent = RedTeamAgent(model_name=red_model)
    blue_agent = BlueTeamAgent(model_name=blue_model)
    orchestrator = OrchestratorAgent(model_name=orchestrator_model)
    
    agents = {"red": red_agent, "blue": blue_agent, "orchestrator": orchestrator}
    workflow = StateGraph(GraphState)
    
    def red_team_node(state: GraphState) -> GraphState:
        logger.info(f"🔴 RED TEAM - Round {state['round_number']}")
        start = time.time()
        decision = red_agent.decide_action(
            simulator=simulator,
            round_num=state["round_number"],
            human_input=state.get("human_input")
        )
        action = decision["action"]
        params = decision["parameters"].copy()
        creativity = decision.get("creativity_type")
        if creativity:
            params["creativity_type"] = creativity
        
        if action == "scan_network":
            result = simulator.scan_network(**params)
        elif action == "exploit_service":
            result = simulator.exploit_service(**params)
        elif action == "establish_persistence":
            result = simulator.establish_persistence(**params)
        elif action == "lateral_move":
            result = simulator.lateral_move(**params)
        elif action == "exfiltrate_data":
            result = simulator.exfiltrate_data(**params)
        else:
            result = {"success": False, "error": f"Unknown action: {action}"}
        
        decision["result"] = result
        decision["execution_time_ms"] = int((time.time() - start) * 1000)
        state["red_decision"] = decision
        state["simulation"] = simulator.get_state()
        state["current_agent"] = "blue"
        state["messages"].append({
            "agent": "red",
            "round": state["round_number"],
            "action": action,
            "success": result.get("success", False),
            "timestamp": time.time()
        })
        return state
    
    def blue_team_node(state: GraphState) -> GraphState:
        logger.info(f"🔵 BLUE TEAM - Round {state['round_number']}")
        start = time.time()
        decision = blue_agent.decide_action(simulator, state["round_number"])
        action = decision["action"]
        params = decision.get("parameters", {})
        
        if action == "detect_anomaly":
            result = simulator.detect_anomaly(**params)
        elif action == "patch_vulnerability":
            result = simulator.patch_vulnerability(**params)
        elif action == "analyze_logs":
            result = simulator.analyze_logs(**params)
        else:
            result = {"success": False, "error": f"Unknown action: {action}"}
        
        decision["result"] = result
        decision["execution_time_ms"] = int((time.time() - start) * 1000)
        state["blue_decision"] = decision
        state["simulation"] = simulator.get_state()
        state["current_agent"] = "orchestrator"
        state["messages"].append({
            "agent": "blue",
            "round": state["round_number"],
            "action": action,
            "success": result.get("success", False),
            "timestamp": time.time()
        })
        return state
    
    def orchestrator_node(state: GraphState) -> GraphState:
        logger.info(f"👁️  ORCHESTRATOR - Round {state['round_number']}")
        decision = orchestrator.evaluate_round(state, simulator)
        state["orchestrator_decision"] = decision
        state["should_continue"] = decision.get("continue_simulation", True)
        state["winner"] = decision.get("winner")
        state["messages"].append({
            "agent": "orchestrator",
            "round": state["round_number"],
            "outcome": decision.get("outcome"),
            "timestamp": time.time()
        })
        return state
    
    def prepare_next_round(state: GraphState) -> GraphState:
        if state.get("should_continue", False):
            state["human_input"] = None
            state["turn_number"] = 0
            state["current_agent"] = "red"
        else:
            state["current_agent"] = "end"
            if state["simulation"]:
                state["simulation"].simulation_active = False
        return state
    
    workflow.add_node("red_team", red_team_node)
    workflow.add_node("blue_team", blue_team_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("prepare_next", prepare_next_round)
    
    workflow.set_entry_point("red_team")
    workflow.add_edge("red_team", "blue_team")
    workflow.add_edge("blue_team", "orchestrator")
    workflow.add_edge("orchestrator", "prepare_next")
    
    def route_next(state: GraphState) -> Literal["red_team", END]:
        if state.get("should_continue", False) and state["round_number"] < max_rounds:
            state["round_number"] += 1
            return "red_team"
        return END
    
    workflow.add_conditional_edges("prepare_next", route_next, {"red_team": "red_team", END: END})
    
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    logger.info("✅ Workflow compiled successfully")
    return app, simulator, agents


def create_initial_state() -> GraphState:
    return {
        "simulation": None,
        "current_agent": "red",
        "round_number": 1,
        "turn_number": 0,
        "red_decision": None,
        "blue_decision": None,
        "orchestrator_decision": None,
        "human_input": None,
        "human_annotations": [],
        "should_continue": True,
        "max_rounds_reached": False,
        "winner": None,
        "messages": [],
        "errors": [],
        "round_start_time": None
    }


def run_simulation(app, initial_state: GraphState, config: Dict[str, Any] = None) -> GraphState:
    """Run the full simulation."""
    if config is None:
        config = {"configurable": {"thread_id": f"sim_{int(time.time())}"}}
    
    logger.info("🚀 Starting simulation")
    final_state = None
    
    try:
        for event in app.stream(initial_state, config, stream_mode="values"):
            final_state = event
        logger.info("✅ Simulation completed")
        return final_state
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise
