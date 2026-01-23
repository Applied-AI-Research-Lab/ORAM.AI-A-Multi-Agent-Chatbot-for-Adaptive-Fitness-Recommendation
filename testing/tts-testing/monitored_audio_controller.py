"""
Enhanced Audio Controller with Performance Monitoring
======================================================

This module extends the standard AudioController to capture detailed timing
metrics for TTS (Text-to-Speech) operations:

1. Request received timestamp
2. OpenAI API call duration
3. Audio file size
4. Response preparation time
5. Total server-side latency

All timing data is logged for performance analysis.
"""

import time
import sys
from pathlib import Path
from flask import request, jsonify

# Add parent directory to path to import original controller
sys.path.append(str(Path(__file__).parent.parent))
from controllers.audio_controller import AudioController


class MonitoredAudioController(AudioController):
    """
    Extended AudioController that captures performance metrics for TTS operations.
    """
    
    def __init__(self, client, log_file_path='testing/tts-testing/results/tts_performance.jsonl'):
        """
        Initialize monitored audio controller.
        
        Args:
            client: OpenAI API client instance
            log_file_path: Path to JSON Lines file for logging metrics
        """
        super().__init__(client)
        self.log_file_path = log_file_path
        
        # Ensure log directory exists
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def speak(self):
        """
        Enhanced speak endpoint with detailed performance monitoring.
        
        Captures:
        - Request reception time
        - Text length (characters, words)
        - OpenAI API call duration
        - Audio file size
        - Total server processing time
        - Response preparation time
        
        Returns same response as parent class but logs all timing metrics.
        """
        import json
        from datetime import datetime
        
        # Capture overall start time
        start_time = time.time()
        request_timestamp = datetime.utcnow().isoformat()
        
        # Initialize metrics dictionary
        metrics = {
            'timestamp': request_timestamp,
            'test_id': None,
            'request_received_at': start_time
        }
        
        # Check if OpenAI client is initialized
        if not self.client:
            metrics['error'] = 'API key not set'
            metrics['success'] = False
            self._log_metrics(metrics)
            return jsonify({'success': False, 'error': 'API key not set'}), 500
        
        try:
            # Parse JSON request body
            parse_start = time.time()
            data = request.get_json()
            metrics['request_parse_time_ms'] = (time.time() - parse_start) * 1000
            
            # Extract text and test ID (if provided)
            text = data.get('text', '')
            metrics['test_id'] = data.get('test_id', None)
            metrics['text_length_chars'] = len(text)
            metrics['text_length_words'] = len(text.split()) if text else 0
            metrics['text_preview'] = text[:50] + '...' if len(text) > 50 else text
            
            # Validate that text was provided
            if not text:
                metrics['error'] = 'No text provided'
                metrics['success'] = False
                metrics['total_server_time_ms'] = (time.time() - start_time) * 1000
                self._log_metrics(metrics)
                return jsonify({'success': False, 'error': 'No text provided'}), 400
            
            # Call OpenAI Text-to-Speech API with timing
            api_call_start = time.time()
            
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            api_call_end = time.time()
            metrics['openai_api_duration_ms'] = (api_call_end - api_call_start) * 1000
            
            # Get audio content and measure size
            audio_content = response.content
            metrics['audio_file_size_bytes'] = len(audio_content)
            metrics['audio_file_size_kb'] = len(audio_content) / 1024
            
            # Calculate total server time
            metrics['total_server_time_ms'] = (time.time() - start_time) * 1000
            metrics['success'] = True
            
            # Log metrics before returning
            self._log_metrics(metrics)
            
            # Return audio file with timing headers
            return audio_content, 200, {
                'Content-Type': 'audio/mpeg',
                'X-Server-Time-Ms': str(int(metrics['total_server_time_ms'])),
                'X-API-Time-Ms': str(int(metrics['openai_api_duration_ms'])),
                'X-Audio-Size-Bytes': str(metrics['audio_file_size_bytes'])
            }
            
        except Exception as e:
            # Log error metrics
            metrics['error'] = str(e)
            metrics['success'] = False
            metrics['total_server_time_ms'] = (time.time() - start_time) * 1000
            self._log_metrics(metrics)
            
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def _log_metrics(self, metrics):
        """
        Write metrics to JSON Lines log file.
        
        Args:
            metrics: Dictionary of timing and performance metrics
        """
        import json
        
        try:
            with open(self.log_file_path, 'a') as f:
                f.write(json.dumps(metrics) + '\n')
        except Exception as e:
            print(f"Error logging metrics: {e}", file=sys.stderr)


def register_monitored_routes(app, openai_client):
    """
    Register monitored TTS endpoint for testing.
    
    Args:
        app: Flask application instance
        openai_client: OpenAI API client
    
    Returns:
        MonitoredAudioController instance
    """
    controller = MonitoredAudioController(openai_client)
    
    # Override the /api/speak endpoint with monitored version
    @app.route('/api/speak/monitored', methods=['POST'])
    def monitored_speak():
        return controller.speak()
    
    return controller
