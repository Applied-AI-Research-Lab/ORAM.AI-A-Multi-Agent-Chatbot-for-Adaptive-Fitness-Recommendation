"""
Agent 2: Fine-tuned Exercise Advisor
Provides specialized exercise suggestions based on user needs and available exercises.
"""


class Agent2ExerciseAdvisor:
    """
    AI Agent 2 - Fine-tuned Exercise Advisor
    
    Uses AI Agent 2 to analyze user needs and suggest appropriate exercises
    based on the exercises retrieved from MCP and conversation context.
    """
    
    def __init__(self, client, model_id="ft:gpt-4.1-mini-2025-04-14:personal::CoQ05d4G"):
        """
        Initialize Agent 2.
        
        Args:
            client: OpenAI API client instance
            model_id: Model ID to use
        """
        self.client = client
        self.model_id = model_id
    
    def suggest_exercises(self, user_message, conversation_context, mcp_exercises):
        """
        Provide specialized exercise suggestions.
        
        Args:
            user_message: The current user message
            conversation_context: List of previous messages
            mcp_exercises: Exercises retrieved from MCP service
            
        Returns:
            dict: {
                "suggestions": str (exercise recommendations),
                "reasoning": str (why these exercises were suggested)
            }
        """
        try:
            # Build prompt for Agent 2
            system_prompt = """You are a fine-tuned AI fitness advisor specialized in recommending exercises.

Based on the user's request and the available exercises from our database, provide intelligent exercise recommendations.

Your recommendations should:
1. Match the user's fitness goals and current level
2. Consider any mentioned limitations or preferences
3. Be practical and achievable
4. Include brief explanations of why each exercise is beneficial

Respond in a friendly, encouraging tone. Keep recommendations concise (2-3 sentences)."""

            # Build messages with context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation context (last 3 messages)
            for msg in conversation_context[-3:]:
                messages.append(msg)
            
            # Add information about available exercises
            exercise_info = "Available exercises from database:\n"
            if mcp_exercises and len(mcp_exercises) > 0:
                for idx, ex in enumerate(mcp_exercises[:5], 1):
                    exercise_info += f"{idx}. {ex.get('name', 'Unknown')} - Targets: {ex.get('muscle', 'N/A')}, Equipment: {ex.get('equipment', 'N/A')}\n"
            else:
                exercise_info += "No specific exercises found in database for this query.\n"
            
            messages.append({
                "role": "system",
                "content": f"Context: {exercise_info}"
            })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages
            )
            
            suggestion_text = response.choices[0].message.content
            
            result = {
                "suggestions": suggestion_text,
                "reasoning": "Based on user request and available exercises"
            }
            
            return result
            
        except Exception as e:
            print(f"Agent 2 Error: {str(e)}")
            return {
                "suggestions": "",
                "reasoning": f"Error generating suggestions: {str(e)}"
            }
