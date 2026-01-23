from flask import request, jsonify
from models import Website, User, Message


class HistoryController:
    """
    ### HistoryController (`history_controller.py`)
    History Controller - Handles chat history endpoints
    Manages conversation history:
    - **GET /chat/history** - Retrieve conversation history for a user
    - **POST /chat/clear** - Clear all chat history for a user
    - Handles message persistence and retrieval
    """
    
    def __init__(self, db):
        """
        Initialize history controller with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_history(self):
        """
        Get conversation history for a specific user.
        
        Request:
            GET /chat/history?userKey={userKey}
            Headers: Authorization: Bearer {api_key}
        
        Response:
            200: {
                "messages": [
                    {
                        "content": str,      # Message text
                        "role": str,         # 'user' or 'assistant'
                        "timestamp": str     # ISO format datetime
                    },
                    ...
                ]
            }
            400: {"error": str}  # Missing userKey parameter
            401: {"error": str}  # Invalid API key
            500: {"error": str}  # Server error
        """
        try:
            print("Received history request")
            
            # Extract and validate API key from Authorization header
            api_key = request.headers.get('Authorization')
            print(f"Authorization header: {api_key}")
            
            # Check if Authorization header exists and has correct format
            if not api_key or not api_key.startswith('Bearer '):
                return jsonify({'error': 'Invalid API key format'}), 401
            
            # Extract the actual API key (remove "Bearer " prefix)
            api_key = api_key.split(' ')[1]
            print(f"Extracted API key: {api_key}")
            
            # Get userKey from query parameters
            user_key = request.args.get('userKey')
            if not user_key:
                return jsonify({'error': 'No user key provided'}), 400

            # Find website by API key
            website = self.db.query(Website).filter_by(api_key=api_key).first()
            if not website:
                return jsonify({'error': 'Invalid API key'}), 401

            # Find user by website and external user ID
            user = self.db.query(User).filter_by(
                website_id=website.id,
                external_user_id=user_key
            ).first()

            # If user doesn't exist, return empty message list
            if not user:
                return jsonify({'messages': []})  # New user, no history

            # Query all messages for this user, ordered by creation time
            messages = self.db.query(Message).filter_by(
                user_id=user.id
            ).order_by(Message.created_at.asc()).all()  # Oldest first

            # Format messages for JSON response
            chat_history = [
                {
                    'content': msg.content,                  # Message text
                    'role': msg.role,                        # 'user' or 'assistant'
                    'timestamp': msg.created_at.isoformat()  # Convert datetime to ISO string
                } for msg in messages
            ]

            # Return formatted message history
            return jsonify({'messages': chat_history})

        except Exception as e:
            # Catch any errors and return as JSON error response
            return jsonify({'error': str(e)}), 500
    
    def clear_history(self):
        """
        Delete all chat history for a specific user.
        
        Request:
            POST /chat/clear
            Headers: Authorization: Bearer {api_key}
            Body: {"userKey": str}
        
        Response:
            200: {"status": "success"}
            400: {"error": str}  # Missing userKey
            401: {"error": str}  # Invalid API key
            500: {"error": str}  # Server error
        """
        try:
            # Extract and validate API key from Authorization header
            api_key = request.headers.get('Authorization')
            if not api_key or not api_key.startswith('Bearer '):
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Extract the actual API key (remove "Bearer " prefix)
            api_key = api_key.split(' ')[1]

            # Parse JSON request body
            data = request.get_json()
            if not data or 'userKey' not in data:
                return jsonify({'error': 'Missing user key'}), 400

            # Find website by API key
            website = self.db.query(Website).filter_by(api_key=api_key).first()
            if not website:
                return jsonify({'error': 'Invalid API key'}), 401

            # Find user by website and external user ID
            user = self.db.query(User).filter_by(
                website_id=website.id,
                external_user_id=data['userKey']
            ).first()

            # If user exists, delete all their messages
            if user:
                # Delete all messages associated with this user
                self.db.query(Message).filter_by(user_id=user.id).delete()
                self.db.commit()  # Commit the deletion

            # Return success (even if user didn't exist - idempotent operation)
            return jsonify({'status': 'success'})

        except Exception as e:
            # Catch any errors and return as JSON error response
            return jsonify({'error': str(e)}), 500
