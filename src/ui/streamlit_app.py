"""
Streamlit UI for Local Adversarial Arena.
Interactive dashboard for running simulations and viewing results.
"""

import streamlit as st
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.graph.workflow import create_workflow, create_initial_state, run_simulation
from src.config import (
    RED_TEAM_MODEL, BLUE_TEAM_MODEL, ORCHESTRATOR_MODEL,
    MAX_ROUNDS, validate_config
)
from src.utils.logger import setup_logger

logger = setup_logger("ui.streamlit")

# Page config
st.set_page_config(
    page_title="Local Adversarial Arena",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .red-team { color: #ff4b4b; font-weight: bold; }
    .blue-team { color: #4b9eff; font-weight: bold; }
    .orchestrator { color: #9c4bff; font-weight: bold; }
    .metric-card { background-color: #262730; padding: 1rem; border-radius: 0.5rem; }
    .log-entry { font-family: monospace; font-size: 0.85em; padding: 0.25rem; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'workflow' not in st.session_state:
    st.session_state.workflow = None
if 'simulator' not in st.session_state:
    st.session_state.simulator = None
if 'messages' not in st.session_state:
    st.session_state.messages = []


def inject_human_input():
    """Callback for human input injection."""
    if st.session_state.human_input_text:
        st.session_state.pending_human_input = st.session_state.human_input_text
        st.session_state.human_input_text = ""


def main():
    st.title("⚔️ Local Adversarial Arena")
    st.markdown("**Red Team vs Blue Team Simulation** | 100% Local with Ollama")
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        st.subheader("Models")
        red_model = st.text_input("Red Team Model", value=RED_TEAM_MODEL)
        blue_model = st.text_input("Blue Team Model", value=BLUE_TEAM_MODEL)
        orch_model = st.text_input("Orchestrator Model", value=ORCHESTRATOR_MODEL)
        
        # Simulation settings
        st.subheader("Simulation")
        max_rounds = st.slider("Max Rounds", 5, 20, MAX_ROUNDS)
        enable_human = st.checkbox("Enable Human Injection", value=True)
        
        # Validate config
        st.subheader("System Check")
        issues = validate_config()
        if issues:
            for issue in issues:
                st.warning(issue)
        else:
            st.success("✓ Ollama connected")
        
        st.divider()
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start", disabled=st.session_state.simulation_running, 
                        type="primary", use_container_width=True):
                start_simulation(red_model, blue_model, orch_model, max_rounds)
        
        with col2:
            if st.button("🛑 Stop", disabled=not st.session_state.simulation_running,
                        use_container_width=True):
                stop_simulation()
        
        if st.button("🔄 Reset", use_container_width=True):
            reset_simulation()
    
    # Main area
    if not st.session_state.simulation_running and not st.session_state.simulation_results:
        # Welcome screen
        st.markdown("""
        ### Welcome to the Arena
        
        This is a local-first simulation where AI agents battle in a cybersecurity exercise:
        
        - 🔴 **Red Team**: Creative attacker using Ollama to think like a human adversary
        - 🔵 **Blue Team**: Defender that detects, responds, and patches
        - 👁️ **Orchestrator**: Referee that judges rounds and tracks the game state
        
        **Features:**
        - 100% local - no data leaves your machine
        - Creative red teaming with storytelling prompts
        - Human-in-the-loop injection during simulation
        - Export rounds as datasets for annotation
        
        Configure your models in the sidebar and click **Start** to begin.
        """)
        
        # Show example network
        with st.expander("📡 Example Network Topology"):
            st.code("""
web-01 (192.168.1.10) - Apache with CVE-2021-41773
db-01  (192.168.1.20) - MySQL with weak credentials
ws-01  (192.168.1.30) - Windows with EternalBlue
app-01 (192.168.1.40) - Tomcat with CVE-2020-9484
            """)
    
    # Simulation running
    if st.session_state.simulation_running:
        st.info("🔄 Simulation in progress... Check terminal for detailed logs")
        
        # Human injection panel
        if enable_human:
            with st.container():
                st.subheader("💬 Inject Human Guidance")
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text_input(
                        "Enter guidance for the agents:",
                        key="human_input_text",
                        placeholder="e.g., 'Try a supply chain attack' or 'Focus on the database server'",
                        label_visibility="collapsed"
                    )
                with col2:
                    st.button("Inject", on_click=inject_human_input, use_container_width=True)
        
        # Live metrics (placeholder - would update via websocket in real impl)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Round", "—")
        with col2:
            st.metric("Red Score", "—")
        with col3:
            st.metric("Blue Score", "—")
        with col4:
            st.metric("Hosts Compromised", "—")
    
    # Show results if available
    if st.session_state.simulation_results:
        display_results(st.session_state.simulation_results)


def start_simulation(red_model, blue_model, orch_model, max_rounds):
    """Start a new simulation."""
    st.session_state.simulation_running = True
    st.session_state.simulation_results = None
    st.session_state.messages = []
    
    try:
        # Create workflow
        with st.spinner("Initializing agents and workflow..."):
            app, simulator, agents = create_workflow(
                red_model=red_model,
                blue_model=blue_model,
                orchestrator_model=orch_model,
                max_rounds=max_rounds
            )
            
            st.session_state.workflow = app
            st.session_state.simulator = simulator
            st.session_state.agents = agents
        
        # Run simulation
        with st.spinner(f"Running simulation (max {max_rounds} rounds)..."):
            initial_state = create_initial_state()
            
            # Add human input injection point
            if hasattr(st.session_state, 'pending_human_input'):
                initial_state['human_input'] = st.session_state.pending_human_input
                del st.session_state.pending_human_input
            
            final_state = run_simulation(app, initial_state)
            
            # Store results
            st.session_state.simulation_results = {
                'final_state': final_state,
                'simulator': simulator,
                'agents': agents,
                'timestamp': datetime.now().isoformat()
            }
            
            st.session_state.simulation_running = False
            st.success("✅ Simulation complete!")
            st.rerun()
            
    except Exception as e:
        st.session_state.simulation_running = False
        st.error(f"Simulation failed: {str(e)}")
        logger.error(f"Simulation error: {e}", exc_info=True)


def stop_simulation():
    """Stop the current simulation."""
    st.session_state.simulation_running = False
    st.warning("Simulation stopped by user")


def reset_simulation():
    """Reset all simulation state."""
    st.session_state.simulation_running = False
    st.session_state.simulation_results = None
    st.session_state.workflow = None
    st.session_state.simulator = None
    st.session_state.messages = []
    if 'pending_human_input' in st.session_state:
        del st.session_state.pending_human_input
    st.success(" arena reset") 
    st.rerun()


def display_results(results):
    """Display simulation results."""
    final_state = results['final_state']
    simulator = results['simulator']
    agents = results['agents']
    
    # Get final metrics
    posture = simulator.get_security_posture()
    
    st.header("📊 Simulation Results")
    
    # Winner banner
    winner = final_state.get('winner', 'unknown')
    if winner == 'red':
        st.error("🔴 RED TEAM WINS - Network Compromised")
    elif winner == 'blue':
        st.success("🔵 BLUE TEAM WINS - Network Defended")
    else:
        st.info("🤝 DRAW - Close Match")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rounds", len(simulator.rounds))
    with col2:
        st.metric("Red Score", final_state.get('red_decision', {}).get('result', {}).get('red_score', 0))
    with col3:
        st.metric("Blue Score", final_state.get('blue_decision', {}).get('result', {}).get('blue_score', 0))
    with col4:
        st.metric("Compromised", f"{posture['compromised_hosts']}/{posture['total_hosts']}")
    
    # Tabs for detailed views
    tab1, tab2, tab3, tab4 = st.tabs(["📜 Round History", "🖥️ Host Status", "📈 Analytics", "💾 Export"])
    
    with tab1:
        st.subheader("Round-by-Round History")
        for msg in final_state.get('messages', []):
            if msg['agent'] in ['red', 'blue']:
                with st.container():
                    agent_class = "red-team" if msg['agent'] == 'red' else "blue-team"
                    st.markdown(f"<span class='{agent_class}'>{msg['agent'].upper()}</span> - Round {msg['round']}", 
                              unsafe_allow_html=True)
                    st.markdown(f"**Action:** `{msg['action']}`")
                    st.markdown(f"**Reasoning:** {msg['reasoning'][:200]}...")
                    if msg.get('result', {}).get('success'):
                        st.success("✓ Success")
                    else:
                        st.error("✗ Failed")
                    st.divider()
    
    with tab2:
        st.subheader("Host Status")
        for host in simulator.hosts.values():
            status = "🔴 COMPROMISED" if host.compromised else "🟢 SECURE"
            with st.expander(f"{host.hostname} ({host.ip}) - {status}"):
                st.json({
                    "os": host.os,
                    "services": [{"port": s.port, "service": s.service, 
                                "vulnerable": s.vulnerable, "patched": s.patched}
                               for s in host.services],
                    "compromised": host.compromised,
                    "persistence": host.persistence if host.compromised else False
                })
    
    with tab3:
        st.subheader("Agent Performance")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔴 Red Team**")
            red_stats = agents['red'].get_stats()
            st.json(red_stats)
        with col2:
            st.markdown("**🔵 Blue Team**")
            blue_stats = agents['blue'].get_stats()
            st.json(blue_stats)
    
    with tab4:
        st.subheader("Export Data")
        
        # Prepare export data
        export_data = {
            "timestamp": results['timestamp'],
            "winner": winner,
            "rounds": len(simulator.rounds),
            "final_state": posture,
            "messages": final_state.get('messages', []),
            "action_log": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "agent": log.agent,
                    "action": log.action_type,
                    "target": log.target_host,
                    "success": log.success
                }
                for log in simulator.action_log
            ]
        }
        
        # JSON export
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            "📥 Download JSON",
            json_str,
            file_name=f"arena_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # Show preview
        with st.expander("Preview Export Data"):
            st.json(export_data)


if __name__ == "__main__":
    main()
