#!/usr/bin/env python3
"""
ExerciseDB MCP Server

Model Context Protocol server for retrieving exercise data from ExerciseDB API.
Used by LLM to get exercise information based on search queries.
"""

from .exercisedb_client import ExerciseDBClient
from typing import List, Dict, Optional


class ExerciseDBMCP:
    """
    MCP Server for ExerciseDB API integration.
    
    This class provides a simple interface for LLMs to query exercise data
    from the ExerciseDB API and receive structured results.
    
    Example:
        mcp = ExerciseDBMCP()
        exercises = mcp.search("chest push", limit=3)
        if exercises:
            for ex in exercises:
                print(ex['name'])
    """
    
    def __init__(self):
        """Initialize the MCP server with ExerciseDB client."""
        self.client = ExerciseDBClient()
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """
        Search for exercises based on a query string.
        
        Args:
            query: Search term (e.g., "chest push", "leg squat", "back pull")
            limit: Maximum number of exercises to return (default: 3)
            
        Returns:
            List of exercise dictionaries with name, instructions, and details.
            Returns empty list if no results found.
            
        Example:
            >>> mcp = ExerciseDBMCP()
            >>> results = mcp.search("chest push", limit=3)
            >>> if results:
            ...     print(f"Found {len(results)} exercises")
            ... else:
            ...     print("No exercises found")
        """
        try:
            # Search using the ExerciseDB client
            response = self.client.search_exercises(query, limit=limit)
            
            # Check if search was successful
            if response.get('success') and response.get('data'):
                exercises = []
                
                for exercise in response['data']:
                    # Extract relevant information
                    exercise_data = {
                        'name': exercise.get('name', 'Unknown'),
                        'id': exercise.get('exerciseId', ''),
                        'instructions': exercise.get('instructions', []),
                        'target_muscles': exercise.get('targetMuscles', []),
                        'secondary_muscles': exercise.get('secondaryMuscles', []),
                        'body_parts': exercise.get('bodyParts', []),
                        'equipment': exercise.get('equipments', []),
                        'gif_url': exercise.get('gifUrl', '')
                    }
                    exercises.append(exercise_data)
                
                return exercises
            else:
                # No results found
                return []
                
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    
    def get_exercise_names(self, query: str, limit: int = 3) -> List[str]:
        """
        Get just the names of exercises matching the query.
        
        Args:
            query: Search term
            limit: Maximum number of exercise names to return
            
        Returns:
            List of exercise names or empty list if no results
        """
        exercises = self.search(query, limit)
        return [ex['name'] for ex in exercises]
    
    def get_exercise_instructions(self, query: str, limit: int = 3) -> Dict[str, List[str]]:
        """
        Get exercise names mapped to their instructions.
        
        Args:
            query: Search term
            limit: Maximum number of exercises
            
        Returns:
            Dictionary mapping exercise names to their instruction lists
        """
        exercises = self.search(query, limit)
        return {ex['name']: ex['instructions'] for ex in exercises}
    
    def format_for_llm(self, query: str, limit: int = 3) -> str:
        """
        Format exercise results as text for LLM consumption.
        
        Args:
            query: Search term
            limit: Maximum number of exercises
            
        Returns:
            Formatted string with exercise details or message if no results
        """
        exercises = self.search(query, limit)
        
        if not exercises:
            return f"No exercises found for query: '{query}'"
        
        output = f"Found {len(exercises)} exercise(s) for '{query}':\n\n"
        
        for i, ex in enumerate(exercises, 1):
            output += f"{i}. {ex['name'].upper()}\n"
            output += f"   Target Muscles: {', '.join(ex['target_muscles'])}\n"
            output += f"   Equipment: {', '.join(ex['equipment'])}\n"
            
            if ex['instructions']:
                output += f"   Instructions:\n"
                for step_num, instruction in enumerate(ex['instructions'], 1):
                    output += f"      {step_num}. {instruction}\n"
            else:
                output += f"   Instructions: Not available\n"
            
            output += f"   GIF: {ex['gif_url']}\n\n"
        
        return output.strip()
    
    def close(self):
        """Close the ExerciseDB client connection."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# # Example usage / testing
# if __name__ == "__main__":
#     print("ExerciseDB MCP Server - Testing\n")
#     print("=" * 70)
    
#     # Create MCP instance
#     mcp = ExerciseDBMCP()
    
#     # Test search
#     query = "chest push"
#     print(f"\nSearching for: '{query}'\n")
    
#     # Method 1: Get structured data
#     exercises = mcp.search(query, limit=3)
    
#     if exercises:
#         print(f" Found {len(exercises)} exercises\n")
#         for ex in exercises:
#             print(f"- {ex['name']}")
#             print(f"  Targets: {', '.join(ex['target_muscles'])}")
#             print(f"  Equipment: {', '.join(ex['equipment'])}")
#             if ex['instructions']:
#                 print(f"  First step: {ex['instructions'][0][:80]}...")
#             print()
#     else:
#         print(" No exercises found")
    
#     # Method 2: Get formatted text for LLM
#     print("\n" + "=" * 70)
#     print("Formatted for LLM:\n")
#     print(mcp.format_for_llm(query, limit=2))
    
#     # Clean up
#     mcp.close()
    
#     print("\n" + "=" * 70)
#     print(" MCP Server test complete")
