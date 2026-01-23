"""
MCP Exercise Service
Wrapper for fetching exercises from ExerciseDB API via MCP.
"""

import time
from services.mcp_service import ExerciseDBMCP


class MCPExerciseService:
    """
    MCP Service for exercise retrieval.
    
    Fetches exercise data from external API using extracted keywords.
    """
    
    def __init__(self):
        """Initialize the MCP service."""
        self.mcp = ExerciseDBMCP()
    
    def fetch_exercises(self, keyword, limit=5):
        """
        Fetch exercises from external API using extracted keyword.
        
        Args:
            keyword: Search term extracted by Agent 1 (e.g., "abs", "chest push")
            limit: Maximum number of exercises to retrieve (default: 5)
            
        Returns:
            dict: {
                "success": bool,
                "exercises": list of exercise dictionaries,
                "count": int,
                "keyword_used": str,
                "mcp_time_ms": float,
                "api_endpoint": str
            }
        """
        start_time = time.time()
        
        try:
            # Use MCP service to search for exercises
            exercises = self.mcp.search(keyword, limit=limit)
            
            end_time = time.time()
            mcp_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            result = {
                "success": True,
                "exercises": exercises,
                "count": len(exercises),
                "keyword_used": keyword,
                "mcp_time_ms": round(mcp_time, 2),
                "api_endpoint": "ExerciseDB",
                "exercises_summary": [
                    {
                        "name": ex.get("name", "Unknown"),
                        "bodyPart": ex.get("bodyPart", "Unknown"),
                        "target": ex.get("target", "Unknown"),
                        "equipment": ex.get("equipment", "Unknown")
                    } for ex in exercises[:3]  # First 3 exercises for summary
                ]
            }
            
            return result
            
        except Exception as e:
            end_time = time.time()
            mcp_time = (end_time - start_time) * 1000
            
            print(f"MCP Service Error: {str(e)}")
            # Return empty result if MCP fails
            return {
                "success": False,
                "exercises": [],
                "count": 0,
                "keyword_used": keyword,
                "mcp_time_ms": round(mcp_time, 2),
                "api_endpoint": "ExerciseDB",
                "error": str(e)
            }
