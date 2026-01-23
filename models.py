# Database Models for ORAM.AI Chatbot
# Defines tables for users, messages, and API keys using SQLAlchemy ORM

# Import SQLAlchemy components for database operations
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
# create_engine: Creates database connection
# Column: Defines table columns
# Integer, String, Text, DateTime: Column data types
# ForeignKey: Creates relationships between tables

from sqlalchemy.ext.declarative import declarative_base  # Base class for ORM models
from sqlalchemy.orm import sessionmaker, relationship     # Session management and relationships
from datetime import datetime  # For timestamp creation
import os                      # For environment variable access

# Create base class for all ORM models
# All model classes will inherit from this
Base = declarative_base()

class Website(Base):
    """
    Website Model - Represents a client website that uses the chat widget.
    
    Each website gets a unique API key for authentication and security.
    Multiple users can belong to one website (one-to-many relationship).
    """
    # Define the database table name
    __tablename__ = 'websites'

    # Primary key - unique identifier for each website
    id = Column(Integer, primary_key=True)
    
    # Website display name (e.g., "Fitness Gym Alpha")
    name = Column(Text)
    
    # Unique API key for authentication
    # Used to validate widget requests and control access
    # Must be unique across all websites
    api_key = Column(Text, unique=True)
    
    # Timestamp when website was registered
    # Automatically set to current UTC time when record is created
    created_at = Column(DateTime, default=datetime.utcnow)

    # One-to-many relationship: One website has many users
    # back_populates creates bidirectional relationship with User.website
    users = relationship("User", back_populates="website")

class User(Base):
    """
    User Model - Represents an end user chatting on a client's website.
    
    Each user belongs to one website and can have multiple messages.
    Users are identified by external_user_id (from client's system).
    """
    # Define the database table name
    __tablename__ = 'users'

    # Primary key - unique identifier for each user in our system
    id = Column(Integer, primary_key=True)
    
    # Foreign key - links user to their website
    # References the id column in websites table
    website_id = Column(Integer, ForeignKey('websites.id'))
    
    # External user identifier from client's system
    # This is the userKey passed from the chat widget
    # Allows clients to track users without exposing their internal IDs
    external_user_id = Column(Text)
    
    # Timestamp when user first started chatting
    # Automatically set to current UTC time when record is created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Many-to-one relationship: Many users belong to one website
    # Allows accessing user.website to get website details
    website = relationship("Website", back_populates="users")
    
    # One-to-many relationship: One user has many messages
    # Allows accessing user.messages to get all their chat messages
    messages = relationship("Message", back_populates="user")

class Message(Base):
    """
    Message Model - Represents a single message in a conversation.
    
    Messages can be from 'user' (human) or 'assistant' (AI).
    Each message belongs to one user and stores the conversation context.
    """
    # Define the database table name
    __tablename__ = 'messages'

    # Primary key - unique identifier for each message
    id = Column(Integer, primary_key=True)
    
    # Foreign key - links message to the user who owns this conversation
    # References the id column in users table
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Role identifies who sent the message
    # 'user' = message from human user
    # 'assistant' = response from AI
    # 'system' = system prompt (not stored but used in API calls)
    role = Column(String)
    
    # The actual message text content
    # Text type allows for long messages without length limits
    content = Column(Text)
    
    # Timestamp when message was created
    # Automatically set to current UTC time when record is created
    # Used to maintain conversation order
    created_at = Column(DateTime, default=datetime.utcnow)

    # Many-to-one relationship: Many messages belong to one user
    # Allows accessing message.user to get user details
    user = relationship("User", back_populates="messages")

def init_db():
    """
    Initialize the database and return a session for database operations.
    
    This function:
    1. Connects to PostgreSQL using connection string from environment
    2. Creates all tables if they don't exist
    3. Creates a database session for queries
    4. Seeds a test website for development
    
    Returns:
        Session: SQLAlchemy session object for database operations
    """
    # Get PostgreSQL connection string from environment variable
    # Format: postgresql://username:password@host:port/database
    # Example: postgresql://orama_user:password123456@localhost:5432/orama_chat
    database_url = os.getenv('DATABASE_URL')
    
    # Validate that DATABASE_URL is set
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please set it in your .env file. "
            "Example: DATABASE_URL=postgresql://username:password@host:port/database"
        )
    
    # Create database engine - establishes connection to PostgreSQL
    # PostgreSQL connection URL format: postgresql://user:pass@host:port/dbname
    engine = create_engine(database_url)
    
    # Create all tables defined by our models (Website, User, Message)
    # If tables already exist, this does nothing (safe to call multiple times)
    Base.metadata.create_all(engine)
    
    # Create session factory bound to our database engine
    Session = sessionmaker(bind=engine)
    
    # Create a new session instance for database operations
    # This session will be used by the Flask app to query and modify data
    session = Session()
    
    # Seed a test website for development and testing
    # Check if test website already exists to avoid duplicates
    if not session.query(Website).filter_by(api_key='YOUR_API_KEY_HERE').first():
        # Create test website with predefined API key
        # This matches the API key in app.py's ACCESS_CONTROL dictionary
        test_site = Website(name='Test Site', api_key='YOUR_API_KEY_HERE')
        session.add(test_site)    # Add to session
        session.commit()           # Save to database
    
    # Return the session for use in the Flask application
    return session