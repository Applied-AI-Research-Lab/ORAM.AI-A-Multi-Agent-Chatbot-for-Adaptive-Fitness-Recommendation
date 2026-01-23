"""
ExerciseDB API Client

A Python client for interacting with the ExerciseDB API to retrieve exercise details.
Supports searching exercises by terms, filtering by muscles, equipment, body parts, and more.

API Documentation: https://www.exercisedb.dev/docs
"""

import requests
from typing import List, Dict, Optional, Union
from dataclasses import dataclass


@dataclass
class ExerciseSearchParams:
    """Parameters for searching exercises"""
    offset: int = 0
    limit: int = 10
    search: Optional[str] = None
    muscles: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    body_parts: Optional[List[str]] = None
    sort_by: str = "name"
    sort_order: str = "desc"


class ExerciseDBClient:
    """
    Client for interacting with the ExerciseDB API.
    
    Example usage:
        client = ExerciseDBClient()
        
        # Search for exercises with fuzzy matching
        results = client.search_exercises("push")
        
        # Get all exercises with optional search
        exercises = client.get_exercises(search="chest", limit=20)
        
        # Advanced filtering
        filtered = client.filter_exercises(
            muscles=["chest", "triceps"],
            equipment=["dumbbell"],
            search="press"
        )
    """
    
    BASE_URL = "https://www.exercisedb.dev/api/v1"
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the ExerciseDB client.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ExerciseDB-Python-Client/1.0',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            raise
    
    def search_exercises(
        self,
        query: str,
        offset: int = 0,
        limit: int = 10,
        threshold: float = 0.3
    ) -> Dict:
        """
        Search exercises using fuzzy matching across all fields.
        Perfect for when users don't know exact terms.
        
        Args:
            query: Search term to fuzzy match (required)
            offset: Number of exercises to skip (default: 0)
            limit: Maximum exercises to return (1-25, default: 10)
            threshold: Fuzzy search threshold (0=exact, 1=loose, default: 0.3)
            
        Returns:
            Dictionary with 'success', 'metadata', and 'data' keys
            
        Example:
            >>> client = ExerciseDBClient()
            >>> results = client.search_exercises("push", limit=5)
            >>> for exercise in results['data']:
            ...     print(exercise['name'])
        """
        params = {
            'q': query,
            'offset': offset,
            'limit': min(max(1, limit), 25),
            'threshold': threshold
        }
        return self._make_request('exercises/search', params)
    
    def get_exercises(
        self,
        offset: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        sort_by: str = "targetMuscles",
        sort_order: str = "desc"
    ) -> Dict:
        """
        Get all exercises with optional fuzzy search and sorting.
        
        Args:
            offset: Number of exercises to skip (default: 0)
            limit: Maximum exercises to return (1-25, default: 10)
            search: Optional search term for fuzzy matching
            sort_by: Field to sort by (name, exerciseId, targetMuscles, bodyParts, equipments)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dictionary with 'success', 'metadata', and 'data' keys
        """
        params = {
            'offset': offset,
            'limit': min(max(1, limit), 25),
            'sortBy': sort_by,
            'sortOrder': sort_order
        }
        if search:
            params['search'] = search
        
        return self._make_request('exercises', params)
    
    def filter_exercises(
        self,
        offset: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        muscles: Optional[List[str]] = None,
        equipment: Optional[List[str]] = None,
        body_parts: Optional[List[str]] = None,
        sort_by: str = "name",
        sort_order: str = "desc"
    ) -> Dict:
        """
        Advanced filtering of exercises by multiple criteria with fuzzy search.
        
        Args:
            offset: Number of exercises to skip (default: 0)
            limit: Maximum exercises to return (1-25, default: 10)
            search: Optional fuzzy search term
            muscles: List of target muscles to filter by
            equipment: List of equipment to filter by
            body_parts: List of body parts to filter by
            sort_by: Field to sort by (name, exerciseId, targetMuscles, bodyParts, equipments)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dictionary with 'success', 'metadata', and 'data' keys
            
        Example:
            >>> results = client.filter_exercises(
            ...     muscles=["chest", "triceps"],
            ...     equipment=["dumbbell", "barbell"],
            ...     search="press"
            ... )
        """
        params = {
            'offset': offset,
            'limit': min(max(1, limit), 25),
            'sortBy': sort_by,
            'sortOrder': sort_order
        }
        
        if search:
            params['search'] = search
        if muscles:
            params['muscles'] = ','.join(muscles)
        if equipment:
            params['equipment'] = ','.join(equipment)
        if body_parts:
            params['bodyParts'] = ','.join(body_parts)
        
        return self._make_request('exercises/filter', params)
    
    def get_exercise_by_id(self, exercise_id: str) -> Dict:
        """
        Get a specific exercise by its unique ID.
        
        Args:
            exercise_id: Unique exercise identifier
            
        Returns:
            Dictionary with 'success' and 'data' keys
            
        Raises:
            requests.exceptions.HTTPError: If exercise not found (404)
        """
        return self._make_request(f'exercises/{exercise_id}')
    
    def get_exercises_by_muscle(
        self,
        muscle_name: str,
        offset: int = 0,
        limit: int = 10,
        include_secondary: bool = False
    ) -> Dict:
        """
        Get exercises that target a specific muscle.
        
        Args:
            muscle_name: Target muscle name (case-insensitive)
            offset: Number of exercises to skip (default: 0)
            limit: Maximum exercises to return (1-25, default: 10)
            include_secondary: Include exercises where muscle is secondary target
            
        Returns:
            Dictionary with 'success', 'metadata', and 'data' keys
            
        Example:
            >>> results = client.get_exercises_by_muscle("abs", limit=15)
        """
        params = {
            'offset': offset,
            'limit': min(max(1, limit), 25),
            'includeSecondary': str(include_secondary).lower()
        }
        return self._make_request(f'muscles/{muscle_name}/exercises', params)
    
    def get_exercises_by_equipment(
        self,
        equipment_name: str,
        offset: int = 0,
        limit: int = 10
    ) -> Dict:
        """
        Get exercises that use specific equipment.
        
        Args:
            equipment_name: Equipment name (case-insensitive, e.g., "dumbbell")
            offset: Number of exercises to skip (default: 0)
            limit: Maximum exercises to return (1-25, default: 10)
            
        Returns:
            Dictionary with 'success', 'metadata', and 'data' keys
        """
        params = {
            'offset': offset,
            'limit': min(max(1, limit), 25)
        }
        return self._make_request(f'equipments/{equipment_name}/exercises', params)
    
    def get_exercises_by_body_part(
        self,
        body_part_name: str,
        offset: int = 0,
        limit: int = 10
    ) -> Dict:
        """
        Get exercises that target a specific body part.
        
        Args:
            body_part_name: Body part name (case-insensitive, e.g., "upper arms")
            offset: Number of exercises to skip (default: 0)
            limit: Maximum exercises to return (1-25, default: 10)
            
        Returns:
            Dictionary with 'success', 'metadata', and 'data' keys
        """
        params = {
            'offset': offset,
            'limit': min(max(1, limit), 25)
        }
        return self._make_request(f'bodyparts/{body_part_name}/exercises', params)
    
    def get_all_muscles(self) -> Dict:
        """
        Get list of all available muscle names.
        
        Returns:
            Dictionary with 'success' and 'data' keys containing muscle names
        """
        return self._make_request('muscles')
    
    def get_all_equipment(self) -> Dict:
        """
        Get list of all available equipment names.
        
        Returns:
            Dictionary with 'success' and 'data' keys containing equipment names
        """
        return self._make_request('equipments')
    
    def get_all_body_parts(self) -> Dict:
        """
        Get list of all available body part names.
        
        Returns:
            Dictionary with 'success' and 'data' keys containing body part names
        """
        return self._make_request('bodyparts')
    
    def print_exercise_details(self, exercise: Dict) -> None:
        """
        Pretty print exercise details.
        
        Args:
            exercise: Exercise dictionary from API response
        """
        print(f"\n{'='*60}")
        print(f"Exercise: {exercise.get('name', 'N/A')}")
        print(f"{'='*60}")
        print(f"ID: {exercise.get('exerciseId', 'N/A')}")
        print(f"GIF URL: {exercise.get('gifUrl', 'N/A')}")
        print(f"\nTarget Muscles: {', '.join(exercise.get('targetMuscles', []))}")
        print(f"Body Parts: {', '.join(exercise.get('bodyParts', []))}")
        print(f"Equipment: {', '.join(exercise.get('equipments', []))}")
        print(f"Secondary Muscles: {', '.join(exercise.get('secondaryMuscles', []))}")
        
        if 'instructions' in exercise and exercise['instructions']:
            print(f"\nInstructions:")
            for i, instruction in enumerate(exercise['instructions'], 1):
                print(f"  {i}. {instruction}")
        print(f"{'='*60}\n")
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Example usage
    print("ExerciseDB API Client - Example Usage\n")
    
    # Create client
    with ExerciseDBClient() as client:
        # Example 1: Search for "push" exercises
        print("1. Searching for 'push' exercises...")
        try:
            results = client.search_exercises("push", limit=5)
            if results.get('success'):
                print(f"Found {results['metadata']['totalExercises']} total exercises")
                print(f"\nShowing first {len(results['data'])} results:\n")
                for exercise in results['data']:
                    print(f"- {exercise['name']} (ID: {exercise['exerciseId']})")
                    print(f"  Targets: {', '.join(exercise.get('targetMuscles', []))}")
                    print(f"  Equipment: {', '.join(exercise.get('equipments', []))}\n")
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 2: Get exercises for chest muscles
        print("\n2. Getting chest exercises...")
        try:
            chest_exercises = client.get_exercises_by_muscle("chest", limit=3)
            if chest_exercises.get('success'):
                for exercise in chest_exercises['data']:
                    client.print_exercise_details(exercise)
        except Exception as e:
            print(f"Error: {e}")
        
        # Example 3: Filter exercises by multiple criteria
        print("\n3. Filtering dumbbell chest exercises...")
        try:
            filtered = client.filter_exercises(
                muscles=["chest"],
                equipment=["dumbbell"],
                limit=3
            )
            if filtered.get('success'):
                print(f"Found {filtered['metadata']['totalExercises']} exercises")
                for exercise in filtered['data']:
                    print(f"- {exercise['name']}")
        except Exception as e:
            print(f"Error: {e}")
