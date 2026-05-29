"""
LangGraph workflow for the adversarial arena.
Defines the stateful, cyclic graph with Red → Blue → Orchestrator → Repeat.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..env.models import GraphState
from ..env.simulator import NetworkSimulator
from ..agents.red_team import RedTeamAgent
from ..agents.blue_team import BlueTeamAgent
from ..agents.orchestrator import OrchestratorAgent
from ..agents.tools import set_simulator
from ..utils.logger import setup_logger, log_round_summary

logger = setup_logger("graph.workflow")


def create_workflow(red_model: str = None, blue_model: str = None, 
                   orchestrator_model: str = None, max_rounds: int = 15):
    """
    Create the LangGraph workflow for adversarial simulation.
    
    Args:
        red_model: Ollama model for red team
        blue_model: Ollama model for blue team
        orchestrator_model: Ollama model for orchestrator
        max_rounds: Maximum simulation rounds
    
    Returns:
        Compiled LangGraph workflow
    """
    
    # Initialize components
    simulator = NetworkSimulator()
    red_agent = RedTeamAgent(model_name=red_model)
    blue_agent = BlueTeamAgent(model_name=blue_model)
    orchestrator = OrchestratorAgent(model_name=orchestrator_model)
    
    # Set simulator for tools
    set_simulator(simulator)
    
    # Define graph
    workflow = StateGraph(GraphState)
    
    # Node: Red Team Turn
    def red_team_node(state: GraphState) -> GraphState:
        """Red team takes an action."""
        logger.info(f"🔴 Red Team - Round {state['round_number']}")
        
        try:
            # Get decision from red agent
            decision = red_agent.decide_action(
                simulator=simulator,
                round_num=state['round_number'],
                human_input=state.get('human_input')
            )
            
            # Execute the action using tools
            action = decision['action']
            params = decision['parameters']
            creativity_type = decision.get('creativity_type')
            
            # Map action to simulator method with creativity type
            if action == 'scan_network':
                result = simulator.scan_network(**params, creativity_type=creativity_type)
            elif action == 'exploit_service':
                result = simulator.exploit_service(**params, creativity_type=creativity_type)
            elif action == 'establish_persistence':
                result = simulator.establish_persistence(**params, creativity_type=creativity_type)
            else:
                result = {'success': False, 'error': f'Unknown action: {action}'}
            
            # Update state
            state['red_decision'] = {
                **decision,
                'result': result
            }
            state['messages'].append({
                'agent': 'red',
                'action': action,
                'reasoning': decision['reasoning'],
                'result': result,
                'round': state['round_number']
            })
            
            logger.info(f"Red action: {action} -> {'✓' if result.get('success') else '✗'}")
            
        except Exception as e:
            logger.error(f"Red team node failed: {e}")
            state['errors'].append(f"Red team error: {str(e)}")
            state['red_decision'] = {
                'action': 'scan_network',
                'parameters': {'stealth_level': 5},
                'reasoning': 'Error fallback',
                'result': {'success': False, 'error': str(e)}
            }
        
        state['current_agent'] = 'blue'
        return state
    
    # Node: Blue Team Turn
    def blue_team_node(state: GraphState) -> GraphState:
        """Blue team takes a defensive action."""
        logger.info(f"🔵 Blue Team - Round {state['round_number']}")
        
        try:
            decision = blue_agent.decide_action(
                simulator=simulator,
                round_num=state['round_number'],
                human_input=state.get('human_input')
            )
            
            # Execute action
            action = decision['action']
            params = decision['parameters']
            
            if action == 'detect_anomaly':
                result = simulator.detect_anomaly(**params)
            elif action == 'patch_vulnerability':
                result = simulator.patch_vulnerability(**params)
            elif action == 'analyze_logs':
                result = simulator.analyze_logs(**params)
            else:
                result = {'success': False, 'error': f'Unknown action: {action}'}
            
            state['blue_decision'] = {
                **decision,
                'result': result
            }
            state['messages'].append({
                'agent': 'blue',
                'action': action,
                'reasoning': decision['reasoning'],
                'result': result,
                'round': state['round_number']
            })
            
            logger.info(f"Blue action: {action} -> {'✓' if result.get('success') else '✗'}")
            
        except Exception as e:
            logger.error(f"Blue team node failed: {e}")
            state['errors'].append(f"Blue team error: {str(e)}")
            state['blue_decision'] = {
                'action': 'detect_anomaly',
                'parameters': {},
                'reasoning': 'Error fallback',
                'result': {'success': False, 'error': str(e)}
            }
        
        state['current_agent'] = 'orchestrator'
        return state
    
    # Node: Orchestrator Evaluation
    def orchestrator_node(state: GraphState) -> GraphState:
        """Orchestrator evaluates round and determines next steps."""
        logger.info(f"👁️ Orchestrator - Evaluating Round {state['round_number']}")
        
        try:
            evaluation = orchestrator.evaluate_round(
                simulator=simulator,
                round_num=state['round_number'],
                red_action=state['red_decision'],
                red_result=state['red_decision']['result'],
                blue_action=state['blue_decision'],
                blue_result=state['blue_decision']['result']
            )
            
            state['orchestrator_decision'] = evaluation
            state['messages'].append({
                'agent': 'orchestrator',
                'evaluation': evaluation,
                'round': state['round_number']
            })
            
            # Update scores in simulation state
            sim_state = simulator.get_state()
            sim_state.red_score += evaluation['red_points']
            sim_state.blue_score += evaluation['blue_points']
            
            # Log round summary
            log_round_summary(
                logger,
                state['round_number'],
                state['red_decision']['action'],
                state['blue_decision']['action'],
                evaluation['outcome']
            )
            
            # Check continuation conditions
            state['should_continue'] = evaluation['continue_simulation']
            state['max_rounds_reached'] = state['round_number'] >= max_rounds
            
            if not state['should_continue'] or state['max_rounds_reached']:
                # Get final results
                final_results = orchestrator.get_final_results(simulator)
                state['winner'] = final_results['winner']
                logger.info(f"Simulation ending. Winner: {state['winner']}")
            
        except Exception as e:
            logger.error(f"Orchestrator node failed: {e}")
            state['errors'].append(f"Orchestrator error: {str(e)}")
            state['should_continue'] = False
        
        return state
    
    # Node: Prepare Next Round
    def next_round_node(state: GraphState) -> GraphState:
        """Prepare for next round or end simulation."""
        if state['should_continue'] and not state['max_rounds_reached']:
            state['round_number'] += 1
            state['turn_number'] = 1
            state['current_agent'] = 'red'
            state['human_input'] = None  # Clear human input after use
            logger.info(f"Starting Round {state['round_number']}")
        else:
            state['current_agent'] = 'end'
        
        return state
    
    # Add nodes to graph
    workflow.add_node("red_team", red_team_node)
    workflow.add_node("blue_team", blue_team_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("next_round", next_round_node)
    
    # Define edges
    workflow.set_entry_point("red_team")
    
    workflow.add_edge("red_team", "blue_team")
    workflow.add_edge("blue_team", "orchestrator")
    workflow.add_edge("orchestrator", "next_round")
    
    # Conditional edge: continue or end
    def should_continue(state: GraphState) -> str:
        if state.get('should_continue', True) and not state.get('max_rounds_reached', False):
            return "continue"
        else:
            return "end"
    
    workflow.add_conditional_edges(
        "next_round",
        should_continue,
        {
            "continue": "red_team",
            "end": END
        }
    )
    
    # Compile with checkpointing
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    logger.info("Workflow compiled successfully")
    
    return app, simulator, {
        'red': red_agent,
        'blue': blue_agent,
        'orchestrator': orchestrator
    }


def create_initial_state() -> GraphState:
    """Create initial state for a new simulation."""
    return {
        'simulation': None,  # Will be populated by simulator
        'current_agent': 'red',
        'round_number': 1,
        'turn_number': 1,
        'red_decision': None,
        'blue_decision': None,
        'orchestrator_decision': None,
        'human_input': None,
        'human_annotations': [],
        'should_continue': True,
        'max_rounds_reached': False,
        'winner': None,
        'messages': [],
        'errors': []
    }


def run_simulation(app, initial_state: GraphState, config: Dict[str, Any] = None):
    """
    Run a complete simulation.
    
    Args:
        app: Compiled LangGraph workflow
        initial_state: Initial GraphState
        config: Optional config with thread_id for checkpointing
    
    Returns:
        Final state and execution history
    """
    if config is None:
        config = {"configurable": {"thread_id": "simulation-1"}}
    
    logger.info("Starting simulation run")
    
    # Run the workflow
    final_state = None
    for event in app.stream(initial_state, config, stream_mode="values"):
        final_state = event
        # Log progress
        if 'round_number' in event:
            logger.debug(f"Processing round {event['round_number']}")
    
    logger.info("Simulation run complete")
    return final_state
