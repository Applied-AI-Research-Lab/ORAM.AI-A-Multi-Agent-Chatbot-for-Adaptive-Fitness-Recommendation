from flask import request, jsonify
from models import Website, User, Message


class ChatController:
    """
    ### ChatController (`chat_controller.py`)
    Chat Controller - Handles main chat endpoint
    Handles main chat functionality:
    - **POST /chat** - Process user messages and return AI responses
    - Manages conversation context
    - Saves messages to database
    - Supports stealth mode (no database storage)
    """
    
    def __init__(self, db, client, model_id):
        """
        Initialize chat controller with database and OpenAI client.
        
        Args:
            db: SQLAlchemy database session
            client: OpenAI API client instance
            model_id: Model ID for chat completions
        """
        self.db = db
        self.client = client
        self.model_id = model_id
    
    def chat(self):
        """
        Main chat endpoint - Handles user messages and returns AI responses.
        
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
            200: {"response": str}        # AI's response text
            400: {"error": str}           # Missing required fields
            401: {"error": str}           # Invalid API key
            500: {"error": str}           # Server or AI service error
        """
        try:
            print("Received chat request")
            
            # Extract and validate API key from Authorization header
            api_key = request.headers.get('Authorization')
            print(f"Authorization header: {api_key}")
            
            # Check if Authorization header exists and has correct format
            if not api_key or not api_key.startswith('Bearer '):
                return jsonify({'error': 'Invalid API key format'}), 401
            
            # Extract the actual API key (remove "Bearer " prefix)
            api_key = api_key.split(' ')[1]
            print(f"Extracted API key: {api_key}")
            
            # Parse JSON request body
            data = request.get_json()
            print(f"Request data: {data}")

            # Validate required fields in request body
            if not data or 'message' not in data or 'userKey' not in data:
                return jsonify({'error': 'Missing message or user key'}), 400
            
            # Extract optional stealth mode flag (default: False)
            # In stealth mode, messages are not saved to database
            stealth_mode = data.get('stealthMode', False)
            
            # Extract session messages for stealth mode (default: empty list)
            # These are the conversation history from browser's sessionStorage
            session_messages = data.get('sessionMessages', [])

            # Find website by API key in database
            website = self.db.query(Website).filter_by(api_key=api_key).first()
            if not website:
                return jsonify({'error': 'Invalid API key'}), 401

            # Find or create user for this website and external user ID
            user = self.db.query(User).filter_by(
                website_id=website.id,           # User belongs to this website
                external_user_id=data['userKey']  # External ID from client
            ).first()

            # Create new user if doesn't exist
            if not user:
                user = User(website_id=website.id, external_user_id=data['userKey'])
                self.db.add(user)       # Add to session
                self.db.commit()        # Commit to database

            # Save user message to database (unless in stealth mode)
            if not stealth_mode:
                user_message = Message(
                    user_id=user.id,           # Link to user
                    role='user',               # Message is from user
                    content=data['message']    # Message text
                )
                self.db.add(user_message)   # Add to session
                self.db.commit()            # Save to database

            # Build conversation context for OpenAI API
            # Start with system message that defines AI's role and behavior
            messages = [{"role": "system", "content": "You are a helpful AI assistant. Respond to the user in Greek in max 2 sentences."}]
            
            if stealth_mode:
                # In stealth mode: Use messages from browser's sessionStorage
                # These were sent from the client in the request
                messages.extend(session_messages)
            else:
                # In normal mode: Load conversation history from database
                previous_messages = self.db.query(Message).filter_by(
                    user_id=user.id
                ).order_by(Message.created_at.asc()).all()  # Oldest first
                
                # Add each previous message to context
                for msg in previous_messages:
                    messages.append({
                        "role": msg.role,      # 'user' or 'assistant'
                        "content": msg.content  # Message text
                    })
            
            # Add the new user message to context
            messages.append({
                "role": "user",
                "content": data['message']
            })

            try:
                # Call OpenAI Chat Completions API
                completion = self.client.chat.completions.create(
                    model=self.model_id,     # Use configured model
                    messages=messages   # Full conversation context
                )
                # Extract response text from API response
                response = completion.choices[0].message.content
            except Exception as openai_error:
                # Log OpenAI API errors for debugging
                print(f"OpenAI API Error: {str(openai_error)}")
                raise Exception("Error communicating with AI service")

            # Save assistant response to database (unless in stealth mode)
            if not stealth_mode:
                assistant_message = Message(
                    user_id=user.id,        # Link to user
                    role='assistant',       # Message is from AI assistant
                    content=response        # AI's response text
                )
                self.db.add(assistant_message)   # Add to session
                self.db.commit()                 # Save to database

            # Return AI response to client
            return jsonify({'response': response})

        except Exception as e:
            # Catch any errors and return as JSON error response
            return jsonify({'error': str(e)}), 500
