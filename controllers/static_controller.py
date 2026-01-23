from flask import send_from_directory


class StaticController:
    """
    Serves static pages (our demo website for chat my-orama.my-domain.com):
    Static Controller - Handles static file serving endpoints
    - **GET /** - Main integration guide page
    - **GET /demo** - Demo page for testing the widget
    """
    
    def serve_index(self):
        """
        Serve the main index page with integration instructions.
        
        Returns:
            HTML page explaining how to integrate the chat widget
        """
        return send_from_directory('static', 'index.html')
    
    def serve_demo(self):
        """
        Serve the demo page for testing the chat widget.
        
        Returns:
            HTML page with embedded chat widget for testing
        """
        return send_from_directory('.', 'static/demo.html')
