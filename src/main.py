"""
Main CLI entry point for Local Adversarial Arena.
Run simulations from command line with configurable parameters.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .graph.workflow import create_workflow, create_initial_state, run_simulation
from .config import (
    RED_TEAM_MODEL, BLUE_TEAM_MODEL, ORCHESTRATOR_MODEL,
    MAX_ROUNDS, validate_config
)
from .utils.logger import setup_logger, log_simulation_start, log_simulation_end, SimulationLogger

logger = setup_logger("main")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Local Adversarial Arena - Red Team vs Blue Team Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default models
  python -m src.main
  
  # Run 10 rounds with specific models
  python -m src.main --rounds 10 --red-model llama3.2:latest --blue-model llama3.2:3b
  
  # Export results to JSON
  python -m src.main --export results/session.json
  
  # Run with human interaction disabled
  python -m src.main --no-human
        """
    )
    
    parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=MAX_ROUNDS,
        help=f"Maximum number of rounds (default: {MAX_ROUNDS})"
    )
    
    parser.add_argument(
        "--red-model",
        type=str,
        default=RED_TEAM_MODEL,
        help=f"Red team Ollama model (default: {RED_TEAM_MODEL})"
    )
    
    parser.add_argument(
        "--blue-model",
        type=str,
        default=BLUE_TEAM_MODEL,
        help=f"Blue team Ollama model (default: {BLUE_TEAM_MODEL})"
    )
    
    parser.add_argument(
        "--orchestrator-model",
        type=str,
        default=ORCHESTRATOR_MODEL,
        help=f"Orchestrator Ollama model (default: {ORCHESTRATOR_MODEL})"
    )
    
    parser.add_argument(
        "--export", "-e",
        type=str,
        help="Export results to JSON file (e.g., exports/session.json)"
    )
    
    parser.add_argument(
        "--no-human",
        action="store_true",
        help="Disable human-in-the-loop interventions"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Check configuration
    if args.check:
        print("Checking configuration...")
        issues = validate_config()
        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)
        else:
            print("✓ Configuration valid - Ollama is accessible")
            print(f"✓ Red model: {args.red_model}")
            print(f"✓ Blue model: {args.blue_model}")
            print(f"✓ Orchestrator model: {args.orchestrator_model}")
            sys.exit(0)
    
    # Set log level
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # Validate config before starting
    issues = validate_config()
    if issues:
        print("\n⚠️  Configuration warnings:")
        for issue in issues:
            print(f"  {issue}")
        print("\nContinuing anyway in 3 seconds...")
        import time
        time.sleep(3)
    
    # Log startup
    config = {
        "red_model": args.red_model,
        "blue_model": args.blue_model,
        "orchestrator_model": args.orchestrator_model,
        "max_rounds": args.rounds,
        "human_enabled": not args.no_human
    }
    log_simulation_start(logger, config)
    
    try:
        # Create session logger
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with SimulationLogger(session_id) as session_logger:
            # Create workflow
            logger.info("Creating workflow...")
            app, simulator, agents = create_workflow(
                red_model=args.red_model,
                blue_model=args.blue_model,
                orchestrator_model=args.orchestrator_model,
                max_rounds=args.rounds
            )
            
            # Create initial state
            initial_state = create_initial_state()
            
            # Run simulation
            logger.info(f"Starting simulation (max {args.rounds} rounds)...")
            print("\n" + "="*60)
            print("SIMULATION STARTING")
            print("="*60 + "\n")
            
            final_state = run_simulation(app, initial_state)
            
            # Get results
            posture = simulator.get_security_posture()
            final_results = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "config": config,
                "winner": final_state.get("winner", "unknown"),
                "total_rounds": len(simulator.rounds),
                "final_scores": {
                    "red": simulator.get_state().red_score,
                    "blue": simulator.get_state().blue_score
                },
                "final_state": {
                    "compromised_hosts": posture["compromised_hosts"],
                    "total_hosts": posture["total_hosts"],
                    "compromise_percentage": posture["compromise_percentage"],
                    "patched_services": posture["patched_services"],
                    "active_alerts": posture["active_alerts"]
                },
                "agent_stats": {
                    "red": agents["red"].get_stats(),
                    "blue": agents["blue"].get_stats(),
                    "orchestrator": agents["orchestrator"].get_stats()
                }
            }
            
            # Log completion
            log_simulation_end(logger, {
                "rounds": final_results["total_rounds"],
                "red_score": final_results["final_scores"]["red"],
                "blue_score": final_results["final_scores"]["blue"],
                "compromised": posture["compromised_hosts"],
                "total_hosts": posture["total_hosts"],
                "winner": final_results["winner"]
            })
            
            # Print summary
            print("\n" + "="*60)
            print("SIMULATION COMPLETE")
            print("="*60)
            print(f"Winner: {final_results['winner'].upper()}")
            print(f"Rounds: {final_results['total_rounds']}")
            print(f"Final Score - Red: {final_results['final_scores']['red']} | "
                  f"Blue: {final_results['final_scores']['blue']}")
            print(f"Hosts Compromised: {posture['compromised_hosts']}/{posture['total_hosts']} "
                  f"({posture['compromise_percentage']}%)")
            print("="*60 + "\n")
            
            # Export if requested
            if args.export:
                export_path = Path(args.export)
                export_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Add detailed data for export
                final_results["detailed_log"] = [
                    {
                        "timestamp": log.timestamp.isoformat(),
                        "agent": log.agent,
                        "action_type": log.action_type,
                        "target_host": log.target_host,
                        "details": log.details,
                        "success": log.success,
                        "detection_score": log.detection_score
                    }
                    for log in simulator.action_log
                ]
                
                final_results["messages"] = final_state.get("messages", [])
                final_results["alerts"] = [
                    {
                        "id": alert.id,
                        "timestamp": alert.timestamp.isoformat(),
                        "host_id": alert.host_id,
                        "severity": alert.severity,
                        "alert_type": alert.alert_type,
                        "description": alert.description
                    }
                    for alert in simulator.alerts
                ]
                
                with open(export_path, "w") as f:
                    json.dump(final_results, f, indent=2)
                
                print(f"✓ Results exported to: {export_path}")
                logger.info(f"Results exported to {export_path}")
            
            return 0
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
        logger.warning("Simulation interrupted by user")
        return 130
    
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        logger.error(f"Simulation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
