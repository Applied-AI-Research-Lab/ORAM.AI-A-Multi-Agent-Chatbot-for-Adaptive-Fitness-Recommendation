"""
Orchestrator: Final Response Generator
Synthesizes all agent inputs into a coherent final response.
"""


class Orchestrator:
    """
    Orchestrator - Final Response Generator
    
    Uses Orchestrator to combine user message, conversation context,
    and all agent outputs into a natural, helpful response.
    """
    
    def __init__(self, client, model_id="gpt-5.2-2025-12-11"):
        """
        Initialize Orchestrator.
        
        Args:
            client: OpenAI API client instance
            model_id: Model ID to use
        """
        self.client = client
        self.model_id = model_id
    
    def generate_response(self, user_message, conversation_context, 
                         agent1_result=None, mcp_result=None, agent2_result=None):
        """
        Synthesize all agent inputs into a coherent final response.
        
        Args:
            user_message: The current user message
            conversation_context: List of previous messages
            agent1_result: Output from Agent 1 (keyword extractor) - optional
            mcp_result: Output from MCP service (exercises) - optional
            agent2_result: Output from Agent 2 (exercise advisor) - optional
            
        Returns:
            str: Final response to send to user
        """
        try:
            # Build comprehensive prompt for orchestrator
            system_prompt = """You are a helpful AI assistant for a fitness application. 

Your role is to synthesize information from multiple sources and provide clear, helpful responses to users.

You may receive:
1. The user's original question
2. Extracted keywords (if exercise-related)
3. Exercise data from our database
4. Specialized exercise recommendations from our fitness advisor

Your task:
- Combine all this information into a natural, conversational response
- Respond in Greek in a friendly, encouraging tone
- Keep responses concise (max 2-3 sentences)
- If exercise data is provided, briefly mention 1-2 relevant exercises
- For general questions, provide helpful information without mentioning exercises

Be natural - don't mention "agents" or "systems" to the user."""

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation context (last 4 messages for better context)
            for msg in conversation_context[-4:]:
                messages.append(msg)
            
            # Build context information for orchestrator
            context_info = ""
            
            if agent1_result and agent1_result.get("is_exercise_related"):
                context_info += f"\n[Internal: User is asking about exercises. Keyword: '{agent1_result.get('keyword')}']"
            
            if mcp_result and mcp_result.get("success") and mcp_result.get("exercises"):
                exercises = mcp_result.get("exercises", [])
                context_info += f"\n[Internal: Found {len(exercises)} exercises in database"
                if exercises:
                    top_exercises = [ex.get('name', 'Unknown') for ex in exercises[:3]]
                    context_info += f": {', '.join(top_exercises)}"
                context_info += "]"
            
            if agent2_result and agent2_result.get("suggestions"):
                context_info += f"\n[Internal: Fitness advisor suggests: {agent2_result.get('suggestions')}]"
            
            # Add context if we have any
            if context_info:
                messages.append({
                    "role": "system",
                    "content": f"Additional context to help you respond:{context_info}"
                })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages
            )
            
            final_response = response.choices[0].message.content
            return final_response
            
        except Exception as e:
            print(f"Orchestrator Error: {str(e)}")
            # Fallback response
            return "Συγγνώμη, αντιμετώπισα ένα πρόβλημα. Μπορείς να ξαναδοκιμάσεις;"
