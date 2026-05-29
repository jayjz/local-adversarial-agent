"""
src/graph/workflow.py
Production LangGraph Orchestration Layer.

Handles native tool calling for both Red and Blue teams,
proper message state management, and clean cyclic routing.
"""

from typing import Annotated, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
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
    """Build and compile the complete simulation workflow."""
    
    # Initialize core components
    simulator = NetworkSimulator()
    set_simulator(simulator)                    # Critical for tool binding

    red_agent = RedTeamAgent()
    blue_agent = BlueTeamAgent()
    orchestrator = OrchestratorAgent()

    # Tool nodes for automatic execution
    red_tools_node = ToolNode(red_agent.tools)
    blue_tools_node = ToolNode(blue_agent.tools)

    workflow = StateGraph(GraphState)

    # === Nodes ===
    def red_node(state: GraphState) -> GraphState:
        """Red Team decision + tool call preparation."""
        logger.info(f"Round {state.get('round_number', 1)}: Red Team acting")
        response = red_agent.decide_action(state, simulator)
        return {
            "messages": [response],
            "simulation": simulator.get_state()
        }

    def blue_node(state: GraphState) -> GraphState:
        """Blue Team decision + tool call preparation."""
        logger.info(f"Round {state.get('round_number', 1)}: Blue Team defending")
        response = blue_agent.decide_action(state, simulator)
        return {
            "messages": [response],
            "simulation": simulator.get_state()
        }

    def orchestrator_node(state: GraphState) -> GraphState:
        """Deterministic scoring and continuation logic."""
        logger.info(f"Round {state.get('round_number', 1)}: Orchestrator evaluating")
        decision = orchestrator.evaluate_round(state, simulator)
        
        return {
            "should_continue": decision.get("continue_simulation", True),
            "winner": decision.get("winner"),
            "simulation": simulator.get_state()
        }

    # Add nodes
    workflow.add_node("red", red_node)
    workflow.add_node("red_tools", red_tools_node)
    workflow.add_node("blue", blue_node)
    workflow.add_node("blue_tools", blue_tools_node)
    workflow.add_node("orchestrator", orchestrator_node)

    # === Routing Logic ===
    def red_router(state: GraphState) -> Literal["red_tools", "blue"]:
        """Route Red to tools if it called any, otherwise pass to Blue."""
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "red_tools"
        return "blue"

    def blue_router(state: GraphState) -> Literal["blue_tools", "orchestrator"]:
        """Route Blue to tools if it called any, otherwise to Orchestrator."""
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "blue_tools"
        return "orchestrator"

    def orchestrator_router(state: GraphState) -> Literal["red", END]:
        """Continue cycle or end simulation."""
        if (state.get("should_continue", True) and 
            state.get("round_number", 1) < max_rounds):
            state["round_number"] = state.get("round_number", 1) + 1
            return "red"
        return END

    # Connect the graph
    workflow.add_conditional_edges("red", red_router)
    workflow.add_edge("red_tools", "red")          # Loop back after tool execution

    workflow.add_conditional_edges("blue", blue_router)
    workflow.add_edge("blue_tools", "blue")        # Loop back after tool execution

    workflow.add_edge("blue", "orchestrator")
    workflow.add_conditional_edges("orchestrator", orchestrator_router)

    workflow.set_entry_point("red")

    # Compile with memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    logger.info(f"✅ Workflow compiled successfully (max_rounds={max_rounds})")
    return app, simulator, {
        "red": red_agent,
        "blue": blue_agent,
        "orchestrator": orchestrator
    }


def create_initial_state() -> GraphState:
    """Create fresh initial state for a new simulation."""
    return {
        "messages": [],
        "round_number": 1,
        "simulation": {},
        "should_continue": True,
        "winner": None
    }
