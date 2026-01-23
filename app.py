# Flask Backend for ORAM.AI Chatbot
# This application serves the chatbot and handles all chat-related API endpoints

# Import Flask framework components
from flask import Flask
from flask_cors import CORS  # Enable Cross-Origin Resource Sharing for widget embedding
import os  # Access environment variables and file paths
from dotenv import load_dotenv  # Load environment variables from .env file
from openai import OpenAI  # OpenAI API client for chat completions and transcription
from models import init_db  # Database initialization

# Import controllers
from controllers.chat_controller import ChatController
from controllers.agentic_controller import AgenticController
from controllers.history_controller import HistoryController
from controllers.audio_controller import AudioController
from controllers.widget_controller import WidgetController
from controllers.static_controller import StaticController
from controllers.db_controller import DatabaseController
from controllers.auth_controller import AuthController

# Load environment variables from .env file
# Expects OPENAI_API_KEY to be defined
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Configure JSON encoding to preserve UTF-8 characters (Greek, Chinese, etc.)
app.config['JSON_AS_ASCII'] = False

# Enable CORS for all routes - allows widget to be embedded on any domain
# The actual domain validation happens in is_access_allowed() function
CORS(app)

# Initialize PostgreSQL database connection and create tables if needed
# Returns SQLAlchemy session for database operations
db = init_db()

# OpenAI API Configuration
model_id = "gpt-5-mini-2025-08-07"  # Model ID for chat completions (lightweight version for our testing)
# Alternative: "gpt-5-2025-08-07" for more powerful responses
# Or our fine-tuned model
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # Initialize OpenAI client with API key from environment

# ============================================================================
# MASTER ACCESS CONTROL - Configure allowed API keys and domain restrictions
# ============================================================================
# Define API keys and their allowed domains
# If an API key is NOT here -> chat widget will not appear
# If an API key exists -> check if domain is in the allowed list
ACCESS_CONTROL = {
    'YOUR_API_KEY_HERE': [
        'localhost',        # Standard localhost for development servers
        '127.0.0.1',        # IPv4 localhost address
        'my-orama.my-domain.com', # Production domain
        '',                 # Empty string for local HTML files opened directly in browser (file:// protocol without proper domain)
        'file://',          # Explicit file:// protocol for Qt applications and local file access
        'qrc://'            # Qt resource system protocol for embedded HTML files in Qt applications
    ],
}

def is_access_allowed(api_key, domain):
    """
    Check if the API key has access from the specified domain.
    
    Logic:
    1. If API key does NOT exist in ACCESS_CONTROL -> Reject
    2. If API key exists -> Check if domain is in the allowed list
    
    Returns:
        tuple: (allowed: bool, error_message: str or None)
    """
    # Check if API key exists in ACCESS_CONTROL
    if api_key not in ACCESS_CONTROL:
        return False, 'API key not found or not authorized'
    
    # Check if domain is in the allowed domains for this API key
    allowed_domains = ACCESS_CONTROL[api_key]
    if domain not in allowed_domains:
        return False, f'Domain not authorized for this API key. Allowed domains: {", ".join(allowed_domains)}'
    
    # If all checks pass, access is allowed
    return True, None
# ============================================================================

# Initialize Controllers
# The application follows a clean MVC-style architecture where each controller handles a specific domain of functionality.
chat_controller = ChatController(db, client, model_id)
agentic_controller = AgenticController(db, client, model_id)  # Multi-agent orchestration controller
history_controller = HistoryController(db)
audio_controller = AudioController(client)
widget_controller = WidgetController(is_access_allowed)
static_controller = StaticController()
db_controller = DatabaseController(db)
auth_controller = AuthController(db)

# ============================================================================
# Route Definitions
# ============================================================================

# Chat endpoints
@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint - Process user messages and return AI responses."""
    # Original chat controller (single model approach)
    return chat_controller.chat()
    
    # Multi-agent orchestration approach with specialized AI agents
    # return agentic_controller.chat()

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get conversation history for a specific user."""
    return history_controller.get_history()

@app.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Delete all chat history for a specific user."""
    return history_controller.clear_history()

# Audio endpoints
@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio to text using OpenAI Whisper API."""
    return audio_controller.transcribe()

@app.route('/api/speak', methods=['POST'])
def speak():
    """Convert text to speech using OpenAI TTS API."""
    return audio_controller.speak()

# Widget delivery endpoints
@app.route('/embed/chat-loader.js')
def serve_loader():
    """Serve the chat loader script to be embedded on client websites."""
    return widget_controller.serve_loader()

@app.route('/embed/chat.js')
def serve_widget():
    """Serve the main chat widget with security validation and language support."""
    return widget_controller.serve_widget()

# Static page endpoints
@app.route('/')
def index():
    """Serve the main index page with integration instructions."""
    return static_controller.serve_index()

@app.route('/demo')
def demo():
    """Serve the demo page for testing the chat widget."""
    return static_controller.serve_demo()

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    """Register a new user with hashed password."""
    return auth_controller.register()

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """Login with username and password."""
    return auth_controller.login()

@app.route('/api/auth/delete-user', methods=['DELETE'])
def auth_delete_user():
    """Delete a user account."""
    return auth_controller.delete_user()

@app.route('/api/auth/update-user', methods=['PUT'])
def auth_update_user():
    """Update user details."""
    return auth_controller.update_user()

# Database management endpoints
@app.route('/api/orama-db/create-table', methods=['POST'])
def db_create_table():
    """Create a new database table."""
    return db_controller.create_table()

@app.route('/api/orama-db/delete-table', methods=['POST'])
def db_delete_table():
    """Delete an existing database table."""
    return db_controller.delete_table()

@app.route('/api/orama-db/truncate-table', methods=['POST'])
def db_truncate_table():
    """Empty a table by removing all records."""
    return db_controller.truncate_table()

@app.route('/api/orama-db/insert', methods=['POST'])
def db_insert():
    """Insert a new record into a table."""
    return db_controller.insert_record()

@app.route('/api/orama-db/update', methods=['POST'])
def db_update():
    """Update existing records in a table."""
    return db_controller.update_record()

@app.route('/api/orama-db/delete', methods=['POST'])
def db_delete():
    """Delete records from a table."""
    return db_controller.delete_record()

@app.route('/api/orama-db/query', methods=['POST'])
def db_query():
    """Execute a custom SQL query."""
    return db_controller.execute_query()

@app.route('/api/orama-db/tables', methods=['GET'])
def db_list_tables():
    """Get a list of all tables in the database."""
    return db_controller.list_tables()

@app.route('/api/orama-db/table-info', methods=['GET'])
def db_table_info():
    """Get detailed information about a table's structure."""
    return db_controller.get_table_info()

@app.route('/api/orama-db/add-columns', methods=['POST'])
def db_add_columns():
    """Add columns to an existing table if they don't exist."""
    return db_controller.add_columns()

@app.route('/api/orama-db/backup', methods=['GET'])
def db_backup():
    """Get a full backup of the database with all tables and data."""
    return db_controller.get_full_backup()

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Run Flask development server
    # debug=True enables:
    # - Auto-reload on code changes
    # - Detailed error pages
    # - Interactive debugger
    # SOS: Never use debug=True in production
    app.run(debug=False)
