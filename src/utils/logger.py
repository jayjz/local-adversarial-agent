"""
Structured logging for the adversarial arena.
Provides consistent logging across all components.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import LOG_LEVEL, LOG_FORMAT, LOG_DIR


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    
    # Create logs directory if it doesn't exist
    Path(LOG_DIR).mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level or LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (daily rotation)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = Path(LOG_DIR) / f"arena_{today}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def log_round_summary(logger: logging.Logger, round_num: int, 
                     red_action: str, blue_action: str, outcome: str):
    """Log a formatted round summary."""
    logger.info("=" * 60)
    logger.info(f"ROUND {round_num} SUMMARY")
    logger.info("=" * 60)
    logger.info(f"🔴 Red:  {red_action}")
    logger.info(f"🔵 Blue: {blue_action}")
    logger.info(f"📊 Outcome: {outcome}")
    logger.info("=" * 60)


def log_simulation_start(logger: logging.Logger, config: dict):
    """Log simulation startup information."""
    logger.info("=" * 60)
    logger.info("LOCAL ADVERSARIAL ARENA - SIMULATION STARTING")
    logger.info("=" * 60)
    logger.info(f"Red Team Model:    {config.get('red_model', 'unknown')}")
    logger.info(f"Blue Team Model:   {config.get('blue_model', 'unknown')}")
    logger.info(f"Max Rounds:        {config.get('max_rounds', 15)}")
    logger.info(f"Human Injection:   {config.get('human_enabled', False)}")
    logger.info("=" * 60)


def log_simulation_end(logger: logging.Logger, final_state: dict):
    """Log simulation completion."""
    logger.info("=" * 60)
    logger.info("SIMULATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total Rounds:      {final_state.get('rounds', 0)}")
    logger.info(f"Final Score - Red: {final_state.get('red_score', 0)} | Blue: {final_state.get('blue_score', 0)}")
    logger.info(f"Hosts Compromised: {final_state.get('compromised', 0)}/{final_state.get('total_hosts', 0)}")
    logger.info(f"Winner:            {final_state.get('winner', 'unknown').upper()}")
    logger.info("=" * 60)


class SimulationLogger:
    """Context manager for structured simulation logging."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = setup_logger(f"arena.{self.session_id}")
        self.start_time = datetime.now()
    
    def __enter__(self):
        self.logger.info(f"Session {self.session_id} started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        self.logger.info(f"Session {self.session_id} ended (duration: {duration})")
        if exc_type:
            self.logger.error(f"Session ended with error: {exc_val}")
    
    def log_agent_decision(self, agent: str, decision: dict):
        """Log an agent's decision with structured data."""
        self.logger.debug(
            f"{agent.upper()} DECISION: {decision.get('action', 'unknown')} | "
            f"Reasoning: {decision.get('reasoning', '')[:100]}..."
        )
    
    def log_tool_execution(self, tool_name: str, params: dict, result: dict):
        """Log tool execution."""
        success = result.get("success", False)
        self.logger.debug(
            f"TOOL: {tool_name}({params}) -> "
            f"{'SUCCESS' if success else 'FAILED'}"
        )
