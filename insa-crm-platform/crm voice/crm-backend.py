#!/usr/bin/env python3
"""
CRM Voice Assistant Backend
Powered by faster-whisper and Claude Code
"""
import os
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
import logging

# Import session and auth managers
from session_manager import get_session_manager
from auth_manager import get_auth_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web UI

# Configuration
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL_SIZE', 'base')
WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cpu')
WHISPER_COMPUTE_TYPE = os.getenv('WHISPER_COMPUTE_TYPE', 'int8')
CLAUDE_CODE_PATH = os.getenv('CLAUDE_CODE_PATH', 'claude')
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB

# Initialize session and auth managers (persistent SQLite storage)
session_mgr = get_session_manager()
auth_mgr = get_auth_manager()

# Initialize Whisper model
logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE} on {WHISPER_DEVICE}")
whisper_model = None

def load_whisper_model(model_size=WHISPER_MODEL_SIZE):
    """Load or reload Whisper model"""
    global whisper_model
    try:
        whisper_model = WhisperModel(
            model_size,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )
        logger.info(f"Whisper model loaded successfully: {model_size}")
        return True
    except Exception as e:
        logger.error(f"Error loading Whisper model: {e}")
        return False

# Load model on startup
load_whisper_model()


def transcribe_audio(audio_path, language=None, model_size=None):
    """
    Transcribe audio file using faster-whisper
    
    Args:
        audio_path: Path to audio file
        language: Language code (e.g., 'en', 'es')
        model_size: Override default model size
    
    Returns:
        Transcription text
    """
    global whisper_model
    
    # Reload model if size changed
    if model_size and model_size != WHISPER_MODEL_SIZE:
        load_whisper_model(model_size)
    
    try:
        logger.info(f"Transcribing audio: {audio_path}")
        
        # Transcribe
        segments, info = whisper_model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                threshold=0.5,
                min_speech_duration_ms=250,
                min_silence_duration_ms=2000
            )
        )
        
        # Combine segments
        transcription = " ".join([segment.text for segment in segments])
        
        logger.info(f"Transcription complete. Language: {info.language}, Duration: {info.duration:.2f}s")
        logger.info(f"Transcribed text: {transcription[:100]}...")
        
        return transcription.strip()
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise


def query_claude_code(text, session_id='default', user_id=None):
    """
    Process CRM query and generate response using INSA Agents Hub

    Args:
        text: Input text/query
        session_id: Session identifier for persistent storage
        user_id: User ID (optional, for authenticated sessions)

    Returns:
        CRM response from appropriate agent
    """
    try:
        logger.info(f"Processing query for session {session_id}: {text[:100]}...")

        # Load session from database
        session_data = session_mgr.get_session(session_id)

        # Import INSA Agents Hub
        from insa_agents import process_query

        # Check if this is a follow-up question (short query without keywords)
        text_lower = text.lower()
        is_followup = (
            len(text) < 50 and
            session_data['last_agent'] == 'sizing' and
            any(word in text_lower for word in [
                'que', 'cual', 'como', 'donde', 'cuando', 'por que',
                'what', 'which', 'how', 'where', 'when', 'why',
                'mas', 'more', 'detalle', 'detail', 'informacion', 'information',
                'necesitas', 'need', 'requiere', 'require'
            ])
        )

        # If it's a follow-up to sizing, provide guidance
        if is_followup:
            logger.info("🔄 Detected follow-up question for sizing agent")
            response = """Para dimensionar correctamente el proyecto, necesito:

📋 **Información Básica:**
• Tipo de servicio (calibración, instrumentación, automatización, etc)
• Cliente o campo petrolero
• Ubicación (si es relevante para logística)

🔧 **Detalles Técnicos:**
• Cantidad de equipos/instrumentos
• Tipo de equipos (transmisores, válvulas, PLCs, etc)
• Alcance del trabajo (instalación, configuración, puesta en marcha)

💡 **Ejemplo de consulta completa:**
"Dimensiona servicio de calibración de 15 transmisores de presión Rosemount en campo La Punta, incluye transporte y certificados"

O simplemente dime: **"Dimensiona servicio de calibración de transmisores"** y trabajaré con la información disponible."""

            session_data['last_query'] = text
            session_mgr.save_session(session_id, session_data)
            return response

        # Route query to appropriate agent, passing session context
        result = process_query(text, session=session_data['sizing_session'])

        # Update session data
        session_data['last_agent'] = result['agent']
        session_data['last_query'] = text
        session_data['context'] = result.get('data', {})

        # Update sizing session if agent returned session updates
        if 'session' in result:
            session_data['sizing_session'] = result['session']

        # Save updated session to database (with user_id if authenticated)
        session_mgr.save_session(session_id, session_data, user_id=user_id)

        logger.info(f"✅ Handled by {result['agent']} agent (confidence: {result['confidence']:.0%})")

        return result['response']

    except ImportError:
        # Fallback to basic responses if agents not available
        logger.warning("INSA Agents Hub not available, using fallback responses")
        text_lower = text.lower()

        # CRM Information queries
        if any(word in text_lower for word in ['what is', 'tell me about', 'describe']):
            if 'insa crm' in text_lower or 'platform' in text_lower:
                return """INSA CRM Platform is an AI-powered industrial automation CRM ecosystem featuring:

• AI Lead Qualification (0-100 scoring)
• ERPNext Integration (complete sales cycle)
• Mautic Marketing Automation (campaigns, emails)
• n8n Workflow Automation (process orchestration)
• InvenTree Inventory Management (BOM, parts)
• Voice Interface (this system!)

All integrated, all automated, all AI-powered.
Running on: http://100.100.101.1

Available services:
- INSA CRM Core: :8003
- ERPNext: :9000
- Mautic: :9700
- n8n: :5678
- InvenTree: :9600"""

        # Feature queries
        if 'feature' in text_lower or 'can you' in text_lower or 'capabilities' in text_lower:
            return """The CRM Voice Assistant can help you with:

🎤 Voice Commands:
• Find customers and leads
• Create new opportunities
• Schedule follow-ups
• View pipeline status
• Generate reports

🤖 AI-Powered Features:
• Lead scoring (0-100 scale)
• Intelligent routing
• Automated workflows
• Multi-channel communication

📊 Data Access:
• Customer information
• Sales pipeline
• Marketing campaigns
• Inventory status
• Project tracking

Try saying: "Find customer Acme Corp" or "Show my pipeline"""

        # Pipeline/Sales queries
        if 'pipeline' in text_lower or 'deals' in text_lower or 'opportunities' in text_lower:
            return """To view your pipeline, I can help you access:

📊 ERPNext CRM (port 9000):
• Active opportunities
• Deal stages and values
• Closing dates
• Customer information

To get live data, I need to integrate with the ERPNext API.
For now, you can access: http://100.100.101.1:9000

Or ask me to "list opportunities" once API integration is complete."""

        # Customer queries
        if 'customer' in text_lower or 'find' in text_lower:
            if 'find' in text_lower:
                return """To find a customer, I can search ERPNext CRM.

Example: "Find customer Acme Corporation"

I'll search for:
• Customer name
• Contact information
• Recent orders
• Open opportunities
• Account status

ERPNext API integration coming soon!
Access manually: http://100.100.101.1:9000"""

        # Lead queries
        if 'lead' in text_lower:
            return """INSA CRM Lead Management:

✅ AI Lead Scoring (0-100):
• Industry fit
• Company size
• Budget indicators
• Engagement level
• Timeline urgency

Access lead scoring API:
http://100.100.101.1:8003/api/docs

Create leads in ERPNext:
http://100.100.101.1:9000

The AI will automatically score and prioritize leads!"""

        # Help/How to
        if 'help' in text_lower or 'how' in text_lower:
            return """🎤 CRM Voice Assistant Help

Voice Commands You Can Try:
• "What is INSA CRM platform?"
• "Show me my pipeline"
• "Find customer [name]"
• "Create new lead"
• "What are the features?"
• "Help me with [task]"

Keyboard Shortcuts:
• Ctrl+R: Start/stop recording

Access Web UIs:
• INSA CRM: http://100.100.101.1:8003
• ERPNext: http://100.100.101.1:9000
• Mautic: http://100.100.101.1:9700

Need technical help? Check:
~/insa-crm-platform/crm voice/CRM-README.md"""

        # Default response
        return f"""I heard: "{text}"

I can help you with:
• CRM information and features
• Customer and lead management
• Pipeline and opportunity tracking
• System access and documentation

Try asking:
• "What is INSA CRM?"
• "Show me features"
• "How do I find customers?"
• "Help me with pipeline"

Or access the web interfaces directly:
• INSA CRM: http://100.100.101.1:8003
• ERPNext: http://100.100.101.1:9000"""

    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return f"I encountered an error processing your request. Please try again or check the logs."


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'whisper_model': WHISPER_MODEL_SIZE,
        'device': WHISPER_DEVICE,
        'claude_path': CLAUDE_CODE_PATH
    })


@app.route('/auth/register', methods=['POST'])
def register():
    """
    Register a new user

    Expects JSON:
        - username: Unique username
        - email: Unique email address
        - password: Plain text password (will be hashed)
        - full_name: Optional full name

    Returns:
        JSON with success status and user info or error message
    """
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()

        # Validate input
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400

        # Register user
        result = auth_mgr.register_user(username, email, password, full_name or None)

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """
    Authenticate user and create session token

    Expects JSON:
        - username_or_email: Username or email address
        - password: Plain text password

    Returns:
        JSON with success status, token, and user info or error message
    """
    try:
        data = request.get_json()

        username_or_email = data.get('username_or_email', '').strip()
        password = data.get('password', '')

        # Validate input
        if not username_or_email or not password:
            return jsonify({'success': False, 'error': 'Missing username/email or password'}), 400

        # Authenticate user
        result = auth_mgr.login(username_or_email, password)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Login failed'}), 500


@app.route('/auth/logout', methods=['POST'])
def logout():
    """
    Logout user by deleting token

    Expects JSON or header:
        - token: Authentication token (in JSON body or Authorization header)

    Returns:
        JSON with success status
    """
    try:
        # Get token from JSON body or Authorization header
        token = None
        if request.is_json:
            token = request.get_json().get('token')

        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]

        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 400

        # Logout
        success = auth_mgr.logout(token)

        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Logout failed'}), 500

    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


@app.route('/auth/verify', methods=['POST'])
def verify_token():
    """
    Verify authentication token

    Expects JSON or header:
        - token: Authentication token (in JSON body or Authorization header)

    Returns:
        JSON with user info or error
    """
    try:
        # Get token from JSON body or Authorization header
        token = None
        if request.is_json:
            token = request.get_json().get('token')

        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]

        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 400

        # Verify token
        user_info = auth_mgr.verify_token(token)

        if user_info:
            return jsonify({'success': True, 'user': user_info}), 200
        else:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401

    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Verification failed'}), 500


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio and query Claude Code
    
    Expects:
        - audio: Audio file
        - model: Whisper model size (optional)
        - language: Language code (optional)
    
    Returns:
        JSON with transcription and Claude Code response
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Check file size
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)
        
        if file_size > MAX_AUDIO_SIZE:
            return jsonify({'error': 'File too large (max 25MB)'}), 400
        
        # Get parameters
        model_size = request.form.get('model', WHISPER_MODEL_SIZE)
        language = request.form.get('language', None)
        
        logger.info(f"Received audio file: {audio_file.filename}, size: {file_size} bytes")
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Transcribe audio
            transcription = transcribe_audio(temp_path, language, model_size)

            if not transcription:
                return jsonify({
                    'transcription': '',
                    'response': 'No speech detected in audio'
                })

            # Try to get auth token
            token = request.form.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
            user_id = None
            session_id = None

            # If token provided, verify and get user_id
            if token:
                user_info = auth_mgr.verify_token(token)
                if user_info:
                    user_id = user_info['user_id']
                    session_id = f"user_{user_id}"  # Session ID based on user_id
                else:
                    return jsonify({'error': 'Invalid or expired token'}), 401

            # Fallback to IP-based session if not authenticated
            if not session_id:
                session_id = request.form.get('session_id') or request.remote_addr

            # Query Claude Code with session
            response = query_claude_code(transcription, session_id=session_id, user_id=user_id)

            return jsonify({
                'transcription': transcription,
                'response': response,
                'language': language,
                'session_id': session_id,
                'user_id': user_id
            })
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
    
    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def query():
    """
    Direct text query to Claude Code (no transcription)

    Expects:
        - text: Query text
        - token: (optional) Authentication token for user sessions
        - session_id: (optional) Session identifier, defaults to user_id or client IP

    Returns:
        JSON with Claude Code response
    """
    try:
        text = request.form.get('text', '')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Try to get auth token
        token = request.form.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = None
        session_id = None

        # If token provided, verify and get user_id
        if token:
            user_info = auth_mgr.verify_token(token)
            if user_info:
                user_id = user_info['user_id']
                session_id = f"user_{user_id}"  # Session ID based on user_id
                logger.info(f"Authenticated user: {user_info['username']} (ID: {user_id})")
            else:
                return jsonify({'error': 'Invalid or expired token'}), 401

        # Fallback to IP-based session if not authenticated
        if not session_id:
            session_id = request.form.get('session_id') or request.remote_addr

        logger.info(f"Direct query (session {session_id}): {text[:100]}...")

        # Query Claude Code with session
        response = query_claude_code(text, session_id=session_id, user_id=user_id)

        return jsonify({
            'query': text,
            'response': response,
            'session_id': session_id,
            'user_id': user_id
        })

    except Exception as e:
        logger.error(f"Query endpoint error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/models', methods=['GET'])
def list_models():
    """List available Whisper models"""
    models = ['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3']
    return jsonify({
        'models': models,
        'current': WHISPER_MODEL_SIZE
    })


@app.route('/change-model', methods=['POST'])
def change_model():
    """
    Change Whisper model
    
    Expects:
        - model: Model size
    """
    try:
        model_size = request.json.get('model', 'base')
        
        if load_whisper_model(model_size):
            return jsonify({
                'status': 'success',
                'model': model_size
            })
        else:
            return jsonify({'error': 'Failed to load model'}), 500
            
    except Exception as e:
        logger.error(f"Model change error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CRM Voice Assistant Backend')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--model', default='base', help='Whisper model size')
    parser.add_argument('--device', default='cpu', help='Device (cpu/cuda)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Update configuration
    WHISPER_MODEL_SIZE = args.model
    WHISPER_DEVICE = args.device
    
    # Reload model with new settings
    load_whisper_model(args.model)
    
    logger.info(f"Starting CRM Voice Assistant Backend")
    logger.info(f"Host: {args.host}:{args.port}")
    logger.info(f"Whisper Model: {WHISPER_MODEL_SIZE}")
    logger.info(f"Device: {WHISPER_DEVICE}")
    logger.info(f"Claude Code Path: {CLAUDE_CODE_PATH}")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
