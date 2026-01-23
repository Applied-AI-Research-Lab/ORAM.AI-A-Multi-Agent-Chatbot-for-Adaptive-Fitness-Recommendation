from flask import request, send_from_directory, make_response


class WidgetController:
    """
    ### WidgetController (`widget_controller.py`)
    Widget Controller - Handles widget script delivery endpoints
    Manages widget script delivery:
    - **GET /embed/chat-loader.js** - Serve widget loader script
    - **GET /embed/chat.js** - Serve main widget with security validation
    - Handles language file loading (en/el)
    - Implements access control validation
    """
    
    def __init__(self, access_control_func):
        """
        Initialize widget controller with access control function.
        
        Args:
            access_control_func: Function to validate API key and domain
        """
        self.is_access_allowed = access_control_func
    
    def serve_loader(self):
        """
        Serve the chat loader script to be embedded on client websites.
        
        Returns:
            JavaScript file (chat-loader.js)
        """
        return send_from_directory('static', 'chat-loader.js')
    
    def serve_widget(self):
        """
        Serve the main chat widget with security validation and language support.
        
        This endpoint:
        1. Validates API key and domain authorization
        2. Loads the appropriate language file
        3. Concatenates language + widget files
        4. Returns as single JavaScript file
        
        Query Parameters:
            lang (str): Language code ('en' or 'el'), defaults to 'en'
            domain (str): Domain where widget is being loaded
            apikey (str): API key for authentication
        
        Returns:
            200: JavaScript code (language + widget concatenated)
            403: JavaScript with console error (access denied)
        """
        # Extract query parameters from URL
        lang = request.args.get('lang', 'en')      # Language code
        domain = request.args.get('domain', '')    # Requesting domain
        api_key = request.args.get('apikey', '')   # API key
        
        # Validate language parameter to prevent directory traversal attacks
        # Only allow 'en' (English) or 'el' (Greek)
        if lang not in ['en', 'el']:
            lang = 'en'  # Default to English if invalid
        
        # Perform access control check
        # Validates both API key existence and domain authorization
        allowed, error_message = self.is_access_allowed(api_key, domain)
        
        # If access is denied, return error JavaScript
        if not allowed:
            # Return JavaScript that logs error to browser console
            # This provides debugging information without exposing the widget
            error_js = f"""
            console.error('Chat Widget Access Denied: {error_message}');
            console.error('API Key: {api_key}');
            console.error('Domain: {domain}');
            """
            # Create response with JavaScript content type
            response = make_response(error_js)
            response.headers['Content-Type'] = 'application/javascript'
            return response
        
        # Access granted - load and serve the widget
        
        # Load the requested language file
        try:
            # Read language file (en.js or el.js)
            with open(f'static/lang/{lang}.js', 'r', encoding='utf-8') as f:
                lang_js = f.read()
        except FileNotFoundError:
            # If language file not found, fallback to English
            with open('static/lang/en.js', 'r', encoding='utf-8') as f:
                lang_js = f.read()
        
        # Load the main widget JavaScript file
        with open('static/chat-widget.js', 'r', encoding='utf-8') as f:
            widget_js = f.read()
        
        # Concatenate language file before widget file
        # Language must load first because widget references translation object
        combined_js = f"{lang_js}\n\n{widget_js}"
        
        # Create response with combined JavaScript
        response = make_response(combined_js)
        response.headers['Content-Type'] = 'application/javascript'
        return response
