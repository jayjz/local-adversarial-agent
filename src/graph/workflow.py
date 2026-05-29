"""
src/graph/workflow.py

LangGraph orchestration layer.
Controls the full Red → Blue → Orchestrator cycle with proper state management,
error recovery, and checkpointing.
"""

from typing import Dict, Any, Literal
import time

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..env.models import GraphState
from ..env.simulator import NetworkSimulator
from ..agents.red_team import RedTeamAgent
from ..agents.blue_team import BlueTeamAgent
from ..agents.orchestrator import OrchestratorAgent
from ..agents.tools import set_simulator
from ..utils.logger import setup_logger


logger = setup_logger("workflow")


def create_workflow(max_rounds: int = 8):
    """Factory function to create a fully configured simulation graph."""
    simulator = NetworkSimulator()
    set_simulator(simulator)                    # Required for tool binding

    red_agent = RedTeamAgent()
    blue_agent = BlueTeamAgent()
    orchestrator = OrchestratorAgent()

    # Build graph
    workflow = StateGraph(GraphState)

    # Nodes with clear responsibilities
    def red_node(state: GraphState) -> GraphState:
        decision = red_agent.decide_action(state, simulator)
        state["red_decision"] = decision
        state["simulation"] = simulator.get_state()
        return state

    def blue_node(state: GraphState) -> GraphState:
        decision = blue_agent.decide_action(state, simulator)
        state["blue_decision"] = decision
        state["simulation"] = simulator.get_state()
        return state

    def orchestrator_node(state: GraphState) -> GraphState:
        decision = orchestrator.evaluate_round(state, simulator)
        state["orchestrator_decision"] = decision
        state["should_continue"] = decision.get("continue_simulation", True)
        state["winner"] = decision.get("winner")
        return state

    # Add nodes
    workflow.add_node("red", red_node)
    workflow.add_node("blue", blue_node)
    workflow.add_node("orchestrator", orchestrator_node)

    # Edges
    workflow.add_edge("red", "blue")
    workflow.add_edge("blue", "orchestrator")

    # Conditional routing after orchestrator
    def should_continue(state: GraphState) -> Literal["red", END]:
        if (state.get("should_continue", True) and 
            state.get("round_number", 1) < max_rounds):
            state["round_number"] = state.get("round_number", 1) + 1
            return "red"
        return END

    workflow.add_conditional_edges("orchestrator", should_continue)

    workflow.set_entry_point("red")

    # Compile with memory for checkpointing (useful for long simulations)
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    logger.info(f"Workflow compiled successfully. Max rounds: {max_rounds}")
    return app, simulator, {"red": red_agent, "blue": blue_agent, "orchestrator": orchestrator}


def create_initial_state() -> GraphState:
    """Create clean initial state for a new simulation."""
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
        "round_start_time": None,
    }
