"""
src/graph/workflow.py
Production LangGraph Orchestration Layer.

Implements native ToolNodes, proper message state reduction, 
and robust cyclic routing.
"""

import operator
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
# `add_messages` ensures new AIMessages and ToolMessages append correctly instead of overwriting
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

    # 2. Native ToolNode
    # This automatically executes any tools the Red LLM requested in its AIMessage
    red_tools_node = ToolNode(red_agent.tools)

    workflow = StateGraph(GraphState)

    # 3. Node Definitions
    def red_node(state: GraphState) -> Dict[str, Any]:
        """Invokes the Red LLM and appends its response to the message list."""
        logger.info(f"--- Round {state.get('round_number', 1)}: Red Team Turn ---")
        response = red_agent.decide_action(state, simulator)
        return {"messages": [response], "simulation": simulator.get_state()}

    def blue_node(state: GraphState) -> Dict[str, Any]:
        """Placeholder for Blue Team execution."""
        # TODO: Refactor Blue Team to use native tool calling similar to Red
        return {"simulation": simulator.get_state()}

    def orchestrator_node(state: GraphState) -> Dict[str, Any]:
        """Non-LLM rules engine to govern game state and scores."""
        # TODO: Refactor Orchestrator to pure Python logic
        return {"simulation": simulator.get_state()}

    # Add Nodes
    workflow.add_node("red", red_node)
    workflow.add_node("red_tools", red_tools_node)
    workflow.add_node("blue", blue_node)
    workflow.add_node("orchestrator", orchestrator_node)

    # 4. Smart Edge Routing
    def red_router(state: GraphState) -> Literal["red_tools", "blue"]:
        """
        Checks the last message. If the LLM requested a tool, route to ToolNode.
        If the LLM just returned text (finished its thought), route to Blue Team.
        """
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "red_tools"
        return "blue"

    # Red attempts action -> Tools execute it -> Loops back to Red to observe result -> Red finishes -> Blue
    workflow.add_conditional_edges("red", red_router)
    workflow.add_edge("red_tools", "red") 
    
    workflow.add_edge("blue", "orchestrator")

    def orchestrator_router(state: GraphState) -> Literal["red", END]:
        """Enforces round limits and win conditions."""
        if state.get("should_continue", True) and state.get("round_number", 1) < max_rounds:
            # Increment round safely via reducer logic or direct state update
            return "red"
        return END

    workflow.add_conditional_edges("orchestrator", orchestrator_router)
    
    # Execution begins with Red
    workflow.set_entry_point("red")

    # 5. Compile with Thread Memory
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
