"""
Agent Logger
Tracks and logs all agent interactions for debugging and analysis.
"""

import json
import os
from datetime import datetime


class AgentLogger:
    """
    Logger for tracking agent interactions.
    
    Logs all agent actions to both individual session files and daily aggregated logs.
    """
    
    def __init__(self):
        """Initialize the logger."""
        self.agent_logs = []
    
    def log_action(self, agent_name, input_data, output_data, metadata=None):
        """
        Log an agent action.
        
        Args:
            agent_name: Name of the agent (e.g., "Agent1", "MCP", "Agent2", "Orchestrator")
            input_data: What was sent to the agent
            output_data: What the agent returned
            metadata: Additional information
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {}
        }
        self.agent_logs.append(log_entry)
    
    def save_to_file(self, user_key, session_id=None):
        """
        Save agent interaction logs to a JSON file.
        
        Args:
            user_key: Unique user identifier
            session_id: Optional session ID for grouping related interactions
        """
        try:
            # Create logs directory if it doesn't exist
            log_dir = "logs/agent_interactions"
            os.makedirs(log_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"agent_log_{user_key}_{timestamp}.json"
            filepath = os.path.join(log_dir, filename)
            
            # Prepare log data
            log_data = {
                "user_key": user_key,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "interactions": self.agent_logs
            }
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"Agent logs saved to: {filepath}")
            
            # Also append to a daily log file for easier tracking
            daily_log = os.path.join(log_dir, f"daily_log_{datetime.now().strftime('%Y%m%d')}.jsonl")
            with open(daily_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                
        except Exception as e:
            print(f"Error saving agent logs: {str(e)}")
    
    def reset(self):
        """Reset the logs for a new request."""
        self.agent_logs = []
    
    def get_logs(self):
        """Get current logs."""
        return self.agent_logs
