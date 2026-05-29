"""
src/graph/workflow.py
Production LangGraph Orchestration Layer.

Implements native ToolNodes, proper message state reduction, 
and robust cyclic routing for both Red and Blue teams.
"""

from typing import Annotated, TypedDict, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from ..env.simulator import NetworkSimulator
from ..agents.red_team import RedTeamAgent
from ..agents.blue_team import BlueTeamAgent
from ..agents.orchestrator import OrchestratorAgent
from ..agents.tools import set_simulator
from ..utils.logger import setup_logger

logger = setup_logger("workflow")

# 1. Modern Graph State
# `add_messages` ensures new AIMessages and ToolMessages append correctly
class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    round_number: int
    simulation: Dict[str, Any]
    should_continue: bool
    winner: str | None

def create_workflow(max_rounds: int = 8):
    """Factory function to construct the deterministic graph."""
    
    # Initialize Environment
    simulator = NetworkSimulator()
    set_simulator(simulator)  # Binds the active simulator to the tool wrappers

    # Initialize Agents
    red_agent = RedTeamAgent()
    blue_agent = BlueTeamAgent()
    orchestrator = OrchestratorAgent()

    # Native ToolNodes for automatic function execution
    red_tools_node = ToolNode(red_agent.tools)
    blue_tools_node = ToolNode(blue_agent.tools)

    workflow = StateGraph(GraphState)

    # --- Node Definitions ---
    def red_node(state: GraphState) -> Dict[str, Any]:
        logger.info(f"--- Round {state.get('round_number', 1)}: Red Team Turn ---")
        response = red_agent.decide_action(state, simulator)
        return {"messages": [response], "simulation": simulator.get_state()}

    def blue_node(state: GraphState) -> Dict[str, Any]:
        logger.info(f"--- Round {state.get('round_number', 1)}: Blue Team Turn ---")
        response = blue_agent.decide_action(state, simulator)
        return {"messages": [response], "simulation": simulator.get_state()}

    def orchestrator_node(state: GraphState) -> Dict[str, Any]:
        logger.info(f"--- Round {state.get('round_number', 1)}: Orchestrator Evaluation ---")
        decision = orchestrator.evaluate_round(state, simulator)
        return {
            "should_continue": decision.get("continue_simulation", True),
            "winner": decision.get("winner"),
            "simulation": simulator.get_state()
        }

    # Add Nodes
    workflow.add_node("red", red_node)
    workflow.add_node("red_tools", red_tools_node)
    workflow.add_node("blue", blue_node)
    workflow.add_node("blue_tools", blue_tools_node)
    workflow.add_node("orchestrator", orchestrator_node)

    # --- Edge Routing ---

    def red_router(state: GraphState) -> Literal["red_tools", "blue"]:
        """Routes Red to its tools if it asked for one, otherwise ends turn."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "red_tools"
        return "blue"

    def blue_router(state: GraphState) -> Literal["blue_tools", "orchestrator"]:
        """Routes Blue to its tools if it asked for one, otherwise ends turn."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "blue_tools"
        return "orchestrator"

    def orchestrator_router(state: GraphState) -> Literal["red", END]:
        """Enforces round limits and win conditions."""
        if state.get("should_continue", True) and state.get("round_number", 1) < max_rounds:
            # Note: We return the updated state natively in LangGraph v0.2+ via direct state mutation patterns
            state["round_number"] += 1 
            return "red"
        return END

    # Connect the Graph
    workflow.add_conditional_edges("red", red_router)
    workflow.add_edge("red_tools", "red") 
    
    workflow.add_conditional_edges("blue", blue_router)
    workflow.add_edge("blue_tools", "blue")
    
    workflow.add_edge("blue", "orchestrator")
    workflow.add_conditional_edges("orchestrator", orchestrator_router)
    
    workflow.set_entry_point("red")

    # Compile with Thread Memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    logger.info("Workflow compiled with native ToolNodes and Cyclic Routing.")
    return app, simulator, {"red": red_agent, "blue": blue_agent, "orchestrator": orchestrator}

def create_initial_state() -> GraphState:
    """Bootstrap the LangGraph state."""
    return {
        "messages": [],
        "round_number": 1,
        "simulation": {},
        "should_continue": True,
        "winner": None
    }
