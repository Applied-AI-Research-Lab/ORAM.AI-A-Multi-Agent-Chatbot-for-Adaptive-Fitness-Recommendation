from flask import request, jsonify


class AudioController:
    """
    ### AudioController (`audio_controller.py`)
    Audio Controller - Handles speech-to-text and text-to-speech endpoints
    Handles voice features:
    - **POST /api/transcribe** - Convert speech to text using Whisper API
    - **POST /api/speak** - Convert text to speech using OpenAI TTS
    - Supports multiple audio formats
    """
    
    def __init__(self, client):
        """
        Initialize audio controller with OpenAI client.
        
        Args:
            client: OpenAI API client instance
        """
        self.client = client
    
    def transcribe(self):
        """
        Transcribe audio to text using OpenAI Whisper API.
        
        Request:
            POST /api/transcribe
            Content-Type: multipart/form-data
            Body: audio file (formats: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm)
        
        Response:
            200: {"success": True, "transcript": str}
            400: {"success": False, "error": str}  # No audio file
            500: {"success": False, "error": str}  # API or server error
        """
        # Check if OpenAI client is initialized
        if not self.client:
            return jsonify({'success': False, 'error': 'API key not set'}), 500
        
        try:
            # Check if audio file is present in the request
            if 'audio' not in request.files:
                return jsonify({'success': False, 'error': 'No audio'}), 400
            
            # Get the audio file from request
            audio_file = request.files['audio']
            
            # Get filename to determine audio format
            # Default to 'audio.webm' if filename not provided
            filename = audio_file.filename or 'audio.webm'
            
            # Read audio file data into memory
            audio_data = audio_file.read()
            
            # Determine MIME type based on file extension
            # This helps OpenAI API properly decode the audio
            if filename.endswith('.mp4'):
                mime_type = 'audio/mp4'
            elif filename.endswith('.mp3'):
                mime_type = 'audio/mpeg'
            else:
                mime_type = 'audio/webm'  # Default for browser recordings
            
            # Call OpenAI Whisper API for transcription
            # Supported formats: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm
            transcript = self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",              # Transcription model
                file=(filename, audio_data, mime_type),  # Audio file tuple
                language="el"                            # Greek language (ISO 639-1 code)
            )
            
            # Return successful transcription
            return jsonify({'success': True, 'transcript': transcript.text})
            
        except Exception as e:
            # Log error for debugging
            print(f"Transcription error: {str(e)}")
            # Return error response
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def speak(self):
        """
        Convert text to speech using OpenAI TTS API.
        
        Request:
            POST /api/speak
            Body: {"text": str}
        
        Response:
            200: Audio file (audio/mpeg format)
            400: {"success": False, "error": str}  # No text provided
            500: {"success": False, "error": str}  # API or server error
        """
        # Check if OpenAI client is initialized
        if not self.client:
            return jsonify({'success': False, 'error': 'API key not set'}), 500
        
        try:
            # Parse JSON request body
            data = request.get_json()
            
            # Extract text to speak (default to empty string)
            text = data.get('text', '')
            
            # Validate that text was provided
            if not text:
                return jsonify({'success': False, 'error': 'No text provided'}), 400
            
            # Call OpenAI Text-to-Speech API
            response = self.client.audio.speech.create(
                model="tts-1",    # TTS model (faster, lower quality than tts-1-hd)
                voice="alloy",    # Voice option (alloy, echo, fable, onyx, nova, shimmer)
                input=text        # Text to convert to speech
            )
            
            # Return audio file directly as response
            # response.content is the MP3 audio data
            return response.content, 200, {'Content-Type': 'audio/mpeg'}
            
        except Exception as e:
            # Return error as JSON
            return jsonify({'success': False, 'error': str(e)}), 500
