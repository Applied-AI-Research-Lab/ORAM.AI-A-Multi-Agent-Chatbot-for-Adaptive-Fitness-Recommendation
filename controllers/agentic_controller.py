from flask import request, jsonify
from models import Website, User, Message
from services.agentic_service import Agent1KeywordExtractor, Agent2ExerciseAdvisor, Orchestrator
from services.agentic_service.logger import AgentLogger
from services.mcp_service.exercise_service import MCPExerciseService


class AgenticController:
    """
    ### AgenticController (`agentic_controller.py`)
    Multi-Agent Orchestration Controller - Handles chat with specialized AI agents
    
    This controller orchestrates the multi-agent system:
    - AI Agent 1: Analyzes user intent and extracts exercise keywords
    - MCP Service: Fetches exercise data from external API
    - AI Agent 2: Fine-tuned exercise advisor
    - Orchestrator: Synthesizes all inputs into final response
    
    Flow:
    - Exercise-related: User → Agent 1 (keyword) → MCP (data) → Agent 2 (suggestions) → Orchestrator (response)
    - General questions: User → Orchestrator (direct response)
    """
    
    def __init__(self, db, client, model_id):
        """
        Initialize agentic controller with database and OpenAI client.
        
        Args:
            db: SQLAlchemy database session
            client: OpenAI API client instance
            model_id: Default model ID (not used, we use specific models per agent)
        """
        self.db = db
        self.client = client
        
        # Initialize services
        self.agent1 = Agent1KeywordExtractor(client)
        self.agent2 = Agent2ExerciseAdvisor(client)
        self.orchestrator = Orchestrator(client)
        self.mcp_service = MCPExerciseService()
        self.logger = AgentLogger()
    
    def chat(self):
        """
        Main chat endpoint - Handles user messages with multi-agent orchestration.
        
        Flow:
        1. Validate API key and user
        2. Agent 1 analyzes if request is exercise-related
        3. If exercise-related:
           - MCP fetches exercises based on keyword
           - Agent 2 provides specialized suggestions
           - Orchestrator combines all info
        4. If general question:
           - Orchestrator responds directly
        5. Save messages to database and log agent interactions
        
        Request:
            POST /chat
            Headers: Authorization: Bearer {api_key}
            Body: {
                "message": str,           # User's message text
                "userKey": str,           # Unique user identifier
                "stealthMode": bool,      # Optional: If true, don't save to database
                "sessionMessages": list   # Optional: Message history for stealth mode
            }
        
        Response:
            200: {"response": str}        # AI's response
            400: {"error": str}           # Missing required fields
            401: {"error": str}           # Invalid API key
            500: {"error": str}           # Server or AI service error
        """
        try:
            # Reset logger for this request
            self.logger.reset()
            
            print("Received chat request (AgenticController)")
            
            # ===== Step 1: Authentication and Validation =====
            api_key = request.headers.get('Authorization')
            
            if not api_key or not api_key.startswith('Bearer '):
                return jsonify({'error': 'Invalid API key format'}), 401
            
            api_key = api_key.split(' ')[1]
            
            # Parse request body
            data = request.get_json()

            if not data or 'message' not in data or 'userKey' not in data:
                return jsonify({'error': 'Missing message or user key'}), 400
            
            # Extract optional parameters
            stealth_mode = data.get('stealthMode', False)
            session_messages = data.get('sessionMessages', [])

            # Find website by API key
            website = self.db.query(Website).filter_by(api_key=api_key).first()
            if not website:
                return jsonify({'error': 'Invalid API key'}), 401

            # Find or create user
            user = self.db.query(User).filter_by(
                website_id=website.id,
                external_user_id=data['userKey']
            ).first()

            if not user:
                user = User(website_id=website.id, external_user_id=data['userKey'])
                self.db.add(user)
                self.db.commit()

            # Save user message to database (unless in stealth mode)
            if not stealth_mode:
                user_message_record = Message(
                    user_id=user.id,
                    role='user',
                    content=data['message']
                )
                self.db.add(user_message_record)
                self.db.commit()

            # ===== Step 2: Build Conversation Context =====
            conversation_context = []
            
            if stealth_mode:
                conversation_context = session_messages
            else:
                previous_messages = self.db.query(Message).filter_by(
                    user_id=user.id
                ).order_by(Message.created_at.asc()).all()
                
                for msg in previous_messages:
                    conversation_context.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # ===== Step 3: Multi-Agent Orchestration =====
            user_message = data['message']
            
            # Agent 1: Extract keyword and determine if exercise-related
            print("Step 1: Running Agent 1 (Keyword Extractor)...")
            agent1_result = self.agent1.extract_keyword(user_message, conversation_context)
            self.logger.log_action(
                "Agent1_KeywordExtractor",
                {"user_message": user_message, "context_length": len(conversation_context)},
                agent1_result,
                {"model": "gpt-5-mini-2025-08-07"}
            )
            print(f"Agent 1 Result: {agent1_result}")
            
            # Initialize variables for later stages
            mcp_result = None
            agent2_result = None
            final_response = None
            
            if agent1_result.get("is_exercise_related") and agent1_result.get("keyword"):
                # Exercise-related request - run full pipeline
                print(f"Exercise-related request detected. Keyword: {agent1_result.get('keyword')}")
                
                # MCP: Fetch exercises
                print("Step 2: Fetching exercises from MCP...")
                mcp_result = self.mcp_service.fetch_exercises(agent1_result.get("keyword"))
                self.logger.log_action(
                    "MCP_ExerciseDB",
                    {"keyword": agent1_result.get("keyword"), "limit": 5},
                    mcp_result,
                    {"api": "ExerciseDB"}
                )
                print(f"MCP Result: Found {mcp_result.get('count', 0)} exercises")
                
                # Agent 2: Get specialized suggestions
                print("Step 3: Running Agent 2 (Exercise Advisor)...")
                agent2_result = self.agent2.suggest_exercises(
                    user_message,
                    conversation_context,
                    mcp_result.get("exercises", [])
                )
                self.logger.log_action(
                    "Agent2_ExerciseAdvisor",
                    {"user_message": user_message, "exercise_count": mcp_result.get('count', 0)},
                    agent2_result,
                    {"model": "gpt-4.1-mini-2025-04-14"}
                )
                print(f"Agent 2 Result: {agent2_result.get('suggestions', '')[:100]}...")
                
                # Orchestrator: Combine all information
                print("Step 4: Running Orchestrator...")
                final_response = self.orchestrator.generate_response(
                    user_message,
                    conversation_context,
                    agent1_result,
                    mcp_result,
                    agent2_result
                )
            else:
                # General question - go directly to orchestrator
                print("General question detected - going directly to Orchestrator...")
                final_response = self.orchestrator.generate_response(
                    user_message,
                    conversation_context
                )
            
            # Log orchestrator
            self.logger.log_action(
                "Orchestrator",
                {
                    "user_message": user_message,
                    "has_agent1": agent1_result is not None,
                    "has_mcp": mcp_result is not None,
                    "has_agent2": agent2_result is not None
                },
                {"response": final_response},
                {"model": "o4-mini-2025-04-16"}
            )
            
            print(f"Final Response: {final_response}")

            # ===== Step 4: Save Response and Logs =====
            # Save assistant response to database (unless in stealth mode)
            if not stealth_mode:
                assistant_message = Message(
                    user_id=user.id,
                    role='assistant',
                    content=final_response
                )
                self.db.add(assistant_message)
                self.db.commit()

            # Save agent logs to file for analysis
            self.logger.save_to_file(data['userKey'])

            # Return response to client with agent logs for testing/analysis
            return jsonify({
                'response': final_response,
                'agent_logs': self.logger.get_logs()  # Include agent execution details
            })

        except Exception as e:
            # Log the error
            print(f"AgenticController Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error response
            return jsonify({'error': str(e)}), 500

