from flask import request, jsonify
import hashlib
import secrets


class AuthController:
    """
    Authentication Controller - Handles user registration, login, deletion, and updates
    
    Provides endpoints for:
    - **POST /api/auth/register** - Register a new user with hashed password
    - **POST /api/auth/login** - Login with username and password
    - **DELETE /api/auth/delete-user** - Delete a user account
    - **PUT /api/auth/update-user** - Update user details
    
    Password Security:
    - Passwords are hashed using SHA-256 with a random salt
    - Salt is stored with the hash in the format: salt:hash
    - Plain passwords are never stored in the database
    """
    
    def __init__(self, db):
        """
        Initialize authentication controller with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.engine = db.get_bind()
    
    def _hash_password(self, password, salt=None):
        """
        Hash a password with SHA-256 and a salt.
        
        Args:
            password: Plain text password
            salt: Optional salt (if None, generates a new random salt)
            
        Returns:
            str: Formatted as "salt:hash"
        """
        if salt is None:
            # Generate a random 32-character hex salt
            salt = secrets.token_hex(16)
        
        # Combine salt and password, then hash
        salted_password = f"{salt}{password}"
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        
        # Return in format: salt:hash
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password, stored_hash):
        """
        Verify a password against a stored hash.
        
        Args:
            password: Plain text password to verify
            stored_hash: Stored hash in format "salt:hash"
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            # Extract salt from stored hash
            salt, _ = stored_hash.split(':', 1)
            
            # Hash the provided password with the same salt
            new_hash = self._hash_password(password, salt)
            
            # Compare hashes
            return new_hash == stored_hash
        except Exception:
            return False
    
    def register(self):
        """
        Register a new user with hashed password.
        
        Request:
            POST /api/auth/register
            Body: {
                "username": str,          # Unique username (required)
                "password": str,          # Plain password (required, will be hashed)
                "email": str,             # Email address (required)
                "external_user_id": str,  # External user ID (required)
                "website_id": int         # Website ID (required)
            }
        
        Response:
            201: {
                "message": "User registered successfully",
                "user_id": int,
                "username": str
            }
            400: {"error": str}  # Missing required fields
            409: {"error": str}  # Username already exists
            500: {"error": str}  # Server error
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            external_user_id = data.get('external_user_id')
            website_id = data.get('website_id')
            
            if not username or not password or not email or not external_user_id or website_id is None:
                return jsonify({'error': 'Missing required fields: username, password, email, external_user_id, website_id'}), 400
            
            # Check if username already exists
            from sqlalchemy import text
            check_query = text("SELECT id FROM users WHERE username = :username")
            with self.engine.connect() as conn:
                result = conn.execute(check_query, {'username': username})
                if result.fetchone():
                    return jsonify({'error': 'Username already exists'}), 409
            
            # Hash the password
            hashed_password = self._hash_password(password)
            
            # Insert new user
            insert_query = text("""
                INSERT INTO users (username, password, email, external_user_id, website_id)
                VALUES (:username, :password, :email, :external_user_id, :website_id)
                RETURNING id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(insert_query, {
                    'username': username,
                    'password': hashed_password,
                    'email': email,
                    'external_user_id': external_user_id,
                    'website_id': website_id
                })
                conn.commit()
                user_id = result.fetchone()[0]
            
            return jsonify({
                'message': 'User registered successfully',
                'user_id': user_id,
                'username': username
            }), 201
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
    
    def login(self):
        """
        Login with username and password.
        
        Request:
            POST /api/auth/login
            Body: {
                "username": str,     # Username (required)
                "password": str      # Plain password (required)
            }
        
        Response:
            200: {
                "message": "Login successful",
                "user_id": int,
                "username": str,
                "email": str
            }
            400: {"error": str}  # Missing required fields
            401: {"error": str}  # Invalid credentials
            500: {"error": str}  # Server error
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Missing required fields: username, password'}), 400
            
            # Get user from database
            from sqlalchemy import text
            query = text("""
                SELECT id, username, password, email
                FROM users
                WHERE username = :username
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {'username': username})
                user = result.fetchone()
            
            # Check if user exists
            if not user:
                return jsonify({'error': 'Invalid username or password'}), 401
            
            user_id, db_username, stored_password, email = user
            
            # Verify password
            if not self._verify_password(password, stored_password):
                return jsonify({'error': 'Invalid username or password'}), 401
            
            # Login successful
            return jsonify({
                'message': 'Login successful',
                'user_id': user_id,
                'username': db_username,
                'email': email
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def delete_user(self):
        """
        Delete a user account.
        
        Request:
            DELETE /api/auth/delete-user
            Body: {
                "user_id": int,      # User ID to delete (optional, use user_id OR username)
                "username": str,     # Username to delete (optional, use user_id OR username)
                "password": str,     # Password for verification (required)
                "confirm": bool      # Must be true to confirm deletion (required)
            }
        
        Response:
            200: {
                "message": "User deleted successfully",
                "user_id": int,
                "username": str
            }
            400: {"error": str}  # Missing required fields
            401: {"error": str}  # Invalid password
            404: {"error": str}  # User not found
            500: {"error": str}  # Server error
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            user_id = data.get('user_id')
            username = data.get('username')
            password = data.get('password')
            confirm = data.get('confirm')
            
            if not password or not confirm:
                return jsonify({'error': 'Missing required fields: password, confirm'}), 400
            
            if not user_id and not username:
                return jsonify({'error': 'Must provide either user_id or username'}), 400
            
            if not confirm:
                return jsonify({'error': 'Must set confirm=true to delete user'}), 400
            
            # Get user from database
            from sqlalchemy import text
            if user_id:
                query = text("""
                    SELECT id, username, password, email
                    FROM users
                    WHERE id = :user_id
                """)
                params = {'user_id': user_id}
            else:
                query = text("""
                    SELECT id, username, password, email
                    FROM users
                    WHERE username = :username
                """)
                params = {'username': username}
            
            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                user = result.fetchone()
            
            # Check if user exists
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            db_user_id, db_username, stored_password, email = user
            
            # Verify password
            if not self._verify_password(password, stored_password):
                return jsonify({'error': 'Invalid password'}), 401
            
            # Delete the user
            delete_query = text("DELETE FROM users WHERE id = :user_id")
            with self.engine.connect() as conn:
                conn.execute(delete_query, {'user_id': db_user_id})
                conn.commit()
            
            return jsonify({
                'message': 'User deleted successfully',
                'user_id': db_user_id,
                'username': db_username
            }), 200
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
    
    def update_user(self):
        """
        Update user details.
        
        Request:
            PUT /api/auth/update-user
            Body: {
                "user_id": int,           # User ID to update (optional, use user_id OR username)
                "username": str,          # Username to update (optional, use user_id OR username)
                "current_password": str,  # Current password for verification (required)
                "new_password": str,      # New password (optional)
                "email": str,             # New email (optional)
                "new_username": str,      # New username (optional)
                "external_user_id": str,  # New external user ID (optional)
                "website_id": int         # New website ID (optional)
            }
        
        Response:
            200: {
                "message": "User updated successfully",
                "user_id": int,
                "username": str,
                "updated_fields": [str, ...]
            }
            400: {"error": str}  # Missing required fields or no fields to update
            401: {"error": str}  # Invalid password
            404: {"error": str}  # User not found
            409: {"error": str}  # New username already exists
            500: {"error": str}  # Server error
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            user_id = data.get('user_id')
            username = data.get('username')
            current_password = data.get('current_password')
            
            if not current_password:
                return jsonify({'error': 'Missing required field: current_password'}), 400
            
            if not user_id and not username:
                return jsonify({'error': 'Must provide either user_id or username'}), 400
            
            # Get user from database
            from sqlalchemy import text
            if user_id:
                query = text("""
                    SELECT id, username, password, email, external_user_id, website_id
                    FROM users
                    WHERE id = :user_id
                """)
                params = {'user_id': user_id}
            else:
                query = text("""
                    SELECT id, username, password, email, external_user_id, website_id
                    FROM users
                    WHERE username = :username
                """)
                params = {'username': username}
            
            with self.engine.connect() as conn:
                result = conn.execute(query, params)
                user = result.fetchone()
            
            # Check if user exists
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            db_user_id, db_username, stored_password, db_email, db_external_user_id, db_website_id = user
            
            # Verify current password
            if not self._verify_password(current_password, stored_password):
                return jsonify({'error': 'Invalid current password'}), 401
            
            # Prepare update fields
            update_fields = []
            update_params = {'user_id': db_user_id}
            updated_field_names = []
            
            # Check for new password
            new_password = data.get('new_password')
            if new_password:
                hashed_password = self._hash_password(new_password)
                update_fields.append("password = :password")
                update_params['password'] = hashed_password
                updated_field_names.append('password')
            
            # Check for new email
            new_email = data.get('email')
            if new_email and new_email != db_email:
                update_fields.append("email = :email")
                update_params['email'] = new_email
                updated_field_names.append('email')
            
            # Check for new username
            new_username = data.get('new_username')
            if new_username and new_username != db_username:
                # Check if new username already exists
                check_query = text("SELECT id FROM users WHERE username = :username AND id != :user_id")
                with self.engine.connect() as conn:
                    result = conn.execute(check_query, {'username': new_username, 'user_id': db_user_id})
                    if result.fetchone():
                        return jsonify({'error': 'New username already exists'}), 409
                
                update_fields.append("username = :username")
                update_params['username'] = new_username
                updated_field_names.append('username')
                db_username = new_username  # Update for response
            
            # Check for new external_user_id
            new_external_user_id = data.get('external_user_id')
            if new_external_user_id and new_external_user_id != db_external_user_id:
                update_fields.append("external_user_id = :external_user_id")
                update_params['external_user_id'] = new_external_user_id
                updated_field_names.append('external_user_id')
            
            # Check for new website_id
            new_website_id = data.get('website_id')
            if new_website_id is not None and new_website_id != db_website_id:
                update_fields.append("website_id = :website_id")
                update_params['website_id'] = new_website_id
                updated_field_names.append('website_id')
            
            # Check if there are any fields to update
            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400
            
            # Build and execute update query
            update_query = text(f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = :user_id
            """)
            
            with self.engine.connect() as conn:
                conn.execute(update_query, update_params)
                conn.commit()
            
            return jsonify({
                'message': 'User updated successfully',
                'user_id': db_user_id,
                'username': db_username,
                'updated_fields': updated_field_names
            }), 200
            
        except Exception as e:
            self.db.rollback()
            return jsonify({'error': str(e)}), 500
