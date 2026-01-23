"""
Agent 1: Keyword Extractor
Analyzes user messages to determine if they're exercise-related and extracts keywords.
"""

import json


class Agent1KeywordExtractor:
    """
    AI Agent 1 - Keyword Extractor
    
    Uses AI Agent 1 to determine if user is asking about exercises
    and extract 1-2 word keyword for searching.
    """
    
    def __init__(self, client, model_id="gpt-5-nano-2025-08-07"):
        """
        Initialize Agent 1.
        
        Args:
            client: OpenAI API client instance
            model_id: Model ID to use
        """
        self.client = client
        self.model_id = model_id
    
    def extract_keyword(self, user_message, conversation_context):
        """
        Analyze user message and extract exercise-related keywords.
        
        Args:
            user_message: The current user message
            conversation_context: List of previous messages for context
            
        Returns:
            dict: {
                "is_exercise_related": bool,
                "keyword": str or None (e.g., "abs", "chest push", "legs"),
                "reasoning": str (why this decision was made)
            }
        """
        try:
            # Build prompt for Agent 1
            system_prompt = """You are an AI agent specialized in analyzing user requests about fitness and exercises.

Your task is to determine:
1. Is the user asking about exercises, workouts, or fitness routines?
2. If yes, extract the most relevant keyword (1-2 words maximum) for searching exercises.

Examples:
- "I want to build my abs" → keyword: "abs", is_exercise_related: true
- "Show me chest push exercises" → keyword: "chest push", is_exercise_related: true
- "What exercises for legs?" → keyword: "legs", is_exercise_related: true
- "How are you today?" → keyword: null, is_exercise_related: false
- "What's the weather?" → keyword: null, is_exercise_related: false

You must respond ONLY with a JSON object in this exact format:
{
    "is_exercise_related": true/false,
    "keyword": "extracted keyword" or null,
    "reasoning": "brief explanation"
}"""

            # Build messages with context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation context (last 3 messages for efficiency)
            for msg in conversation_context[-3:]:
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Agent 1 Error: {str(e)}")
            # Default to treating as general question if agent fails
            return {
                "is_exercise_related": False,
                "keyword": None,
                "reasoning": f"Error in keyword extraction: {str(e)}"
            }
