#!/usr/bin/env python3
"""
CRM Voice Assistant Backend
Powered by faster-whisper and Claude Code
"""
import os
import subprocess
import tempfile
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from faster_whisper import WhisperModel
import logging
from jose import jwt, JWTError
from typing import Optional, Dict, Any

# Import session and auth managers
from session_manager import get_session_manager
from auth_manager import get_auth_manager
from session_claude_manager import get_session_claude_manager, build_context_prompt

# Import Prometheus metrics (optional)
try:
    from prometheus_metrics import initialize_metrics, start_metrics_server
    PROMETHEUS_ENABLED = True
except ImportError:
    PROMETHEUS_ENABLED = False
    logging.warning("prometheus_metrics not available, metrics disabled")

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

# JWT Configuration (same as FastAPI auth API)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'insa_crm_secret_key_[REDACTED]_production_change_this')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')

# Initialize session and auth managers (persistent SQLite storage)
session_mgr = get_session_manager()
auth_mgr = get_auth_manager()
claude_mgr = get_session_claude_manager()

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


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token from FastAPI auth API

    Args:
        token: JWT token string

    Returns:
        Dict with user info (user_id, email, role) or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "user")

        if not user_id or not email:
            return None

        return {
            'user_id': user_id,
            'email': email,
            'role': role,
            'username': email.split('@')[0]  # For compatibility
        }
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def get_auth_token_and_verify(request) -> Optional[Dict[str, Any]]:
    """
    Extract and verify auth token from request (supports both JWT and legacy SQLite tokens)

    Args:
        request: Flask request object

    Returns:
        User info dict or None if authentication fails
    """
    # Try to get token from multiple sources
    token = None

    # 1. Authorization header (Bearer token)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')

    # 2. JSON body
    if not token:
        try:
            data = request.get_json(silent=True)
            if data:
                token = data.get('token')
        except Exception as e:
            logger.debug(f"Failed to parse JSON body for token: {e}")

    # 3. Form data
    if not token:
        token = request.form.get('token')

    if not token:
        return None

    # Try JWT verification first (new system)
    user_info = verify_jwt_token(token)
    if user_info:
        logger.debug(f"JWT authentication successful for user: {user_info['email']}")
        return user_info

    # Fallback to legacy SQLite token verification
    user_info = auth_mgr.verify_token(token)
    if user_info:
        logger.debug(f"Legacy token authentication successful for user: {user_info.get('email', 'unknown')}")
        return user_info

    return None


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


def call_claude_code_subprocess(text, agent_context=None, session_history=None):
    """
    Actually call Claude Code CLI via subprocess for LLM responses

    Args:
        text: User query
        agent_context: Which INSA agent domain this relates to (sizing, crm, platform, etc)
        session_history: Previous conversation context

    Returns:
        Claude Code's response string
    """
    # Intelligent timeout selection based on query complexity (moved outside try for error handling)
    text_lower = text.lower()

    # Detect complex design tasks (1 hour timeout)
    complex_keywords = [
        'p&id', 'pid', 'diagrama', 'diagram',
        'hoja de datos', 'datasheet', 'data sheet',
        'cad', '3d', 'modelo', 'model',
        'plano', 'drawing', 'drawings',
        'especificación completa', 'complete specification',
        'proyecto completo', 'complete project',
        'diseño completo', 'complete design',
        'generar todo', 'generate everything',
        'envia', 'send email', 'email'
    ]

    is_complex = any(keyword in text_lower for keyword in complex_keywords)

    if is_complex:
        timeout = 3600  # 1 hour for complex design tasks
        timeout_label = "1 hour"
    else:
        timeout = 540  # 9 minutes for standard queries (✅ INCREASED from 120s to 540s - User requested Oct 30, 2025)
        timeout_label = "9 minutes"

    try:
        # Build context prompt for Claude Code
        context_parts = []

        if agent_context:
            context_parts.append(f"You are INSA AI's {agent_context} agent.")

            # Add agent-specific context
            if agent_context == 'sizing':
                context_parts.append("You help dimension Oil & Gas instrumentation, automation, and calibration projects.")
                context_parts.append("Ask clarifying questions if needed (service type, equipment, location, scope).")
            elif agent_context == 'crm':
                context_parts.append("You help with CRM data: leads, customers, opportunities, quotations.")
                context_parts.append("You have access to ERPNext CRM via MCP tools.")
            elif agent_context == 'platform':
                context_parts.append("You monitor platform health: DefectDojo, ERPNext, Mautic, n8n, Grafana.")
                context_parts.append("You have access to platform-admin MCP tools.")

        # Add conversation history if available (formatted for readability)
        if session_history and len(session_history) > 0:
            context_parts.append("\n## Recent Conversation History:")
            for msg in session_history:
                role_label = "User" if msg['role'] == 'user' else "Assistant"
                agent_label = f" ({msg['agent']} agent)" if msg.get('agent') else ""
                context_parts.append(f"{role_label}{agent_label}: {msg['content']}")
            context_parts.append("")  # Add blank line

        # Build full prompt
        full_prompt = "\n".join(context_parts) + f"\n\nUser query: {text}\n\nRespond in Spanish for Spanish queries, English for English queries. Be concise and helpful."

        if is_complex:
            logger.info(f"🔧 Detected complex design task - Using {timeout_label} timeout")

        logger.info(f"🤖 Calling Claude Code subprocess with context: {agent_context}, timeout: {timeout}s")

        # Call Claude Code via subprocess (use -p for non-interactive, stdin for prompt)
        result = subprocess.run(
            [CLAUDE_CODE_PATH, '-p'],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            response = result.stdout.strip()
            logger.info(f"✅ Claude Code responded ({len(response)} chars)")
            return response
        else:
            logger.error(f"❌ Claude Code failed: {result.stderr}")
            return f"Lo siento, hubo un error procesando tu consulta. (Claude Code error: {result.returncode})"

    except subprocess.TimeoutExpired:
        logger.error(f"❌ Claude Code subprocess timeout (>{timeout}s / {timeout_label})")
        if is_complex:
            return f"Lo siento, la consulta compleja tomó más de {timeout_label}. Este es un proyecto muy extenso que puede requerir dividirlo en fases:\n\n1. Primero generar el P&ID\n2. Luego las hojas de datos de válvulas\n3. Finalmente las especificaciones SDV\n\nO considera usar el sistema de tareas en segundo plano (próximamente)."
        else:
            return f"Lo siento, la consulta tomó más de {timeout_label}. Intenta ser más específico o dividir la consulta."
    except Exception as e:
        logger.error(f"❌ Claude Code subprocess error: {e}")
        return f"Error llamando a Claude Code: {str(e)}"


def query_claude_code(text, session_id='default', user_id=None, file_paths=None):
    """
    Process CRM query using Claude Code LLM via subprocess

    Routes query to determine agent context, then calls actual Claude Code CLI

    Args:
        text: Input text/query
        session_id: Session identifier for persistent storage
        user_id: User ID (optional, for authenticated sessions)
        file_paths: Optional list of uploaded file paths

    Returns:
        Claude Code LLM response
    """
    try:
        logger.info(f"Processing query for session {session_id}: {text[:100]}...")

        # Load session from database
        session_data = session_mgr.get_session(session_id)

        # Import INSA Agents Hub for routing logic
        from insa_agents import process_query

        # Route query to determine which agent should handle it
        # This gives us agent context but we'll use Claude Code for the actual response
        result = process_query(text, session=session_data['sizing_session'])

        agent_type = result['agent']
        logger.info(f"📍 Routed to {agent_type} agent (confidence: {result['confidence']:.0%})")

        # Get recent conversation history for context (last 10 messages = 5 turns)
        recent_messages = session_mgr.get_recent_messages(session_id, limit=10)

        # Convert to simple format with FULL CONTEXT (2000 char limit)
        session_history = []
        for msg in recent_messages:
            session_history.append({
                'role': msg['role'],
                'content': msg['content'][:2000],  # ✅ INCREASED to 2000 chars (10x more context)
                'agent': msg.get('agent')
            })

        # Add current user query to conversation history
        session_mgr.add_message(session_id, 'user', text, agent=agent_type)

        # Build comprehensive context prompt with full history
        full_prompt = build_context_prompt(
            text=text,
            agent_context=agent_type,
            session_history=session_history,
            session_id=session_id
        )

        # Use session-persistent Claude Code instance (lower latency + better context)
        # ✅ TIMEOUT INCREASED: 300s (5 minutes) - User requested change Oct 30, 2025
        # ✅ FILE UPLOAD FIX: Pass file_paths to session manager
        response = claude_mgr.query(
            session_id=session_id,
            prompt=full_prompt,
            timeout=300,  # ✅ INCREASED from 60s to 300s (5 minutes)
            file_paths=file_paths  # ✅ Pass uploaded files
        )

        # Add AI response to conversation history
        session_mgr.add_message(session_id, 'assistant', response, agent=agent_type)

        # ✅ FIX: Reload session_data to get updated conversation_history
        # Without this, we overwrite the messages we just added!
        session_data = session_mgr.get_session(session_id)

        # Update session data
        session_data['last_agent'] = agent_type
        session_data['last_query'] = text
        session_data['context'] = result.get('data', {})

        # Update sizing session if agent returned session updates
        if 'session' in result:
            session_data['sizing_session'] = result['session']

        # Save updated session to database (with user_id if authenticated)
        session_mgr.save_session(session_id, session_data, user_id=user_id)

        logger.info(f"✅ Claude Code response delivered via {agent_type} agent")

        return response

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
    Direct text query to Claude Code (no transcription) with optional file uploads

    Expects:
        - text: Query text
        - token: (optional) Authentication token for user sessions
        - session_id: (optional) Session identifier, defaults to user_id or client IP
        - file_count: (optional) Number of files attached
        - file0, file1, ... fileN: (optional) Attached files

    Returns:
        JSON with Claude Code response
    """
    try:
        text = request.form.get('text', '')
        file_count = int(request.form.get('file_count', 0))

        if not text and file_count == 0:
            return jsonify({'error': 'No text or files provided'}), 400

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

        # Handle file uploads
        uploaded_files = []
        temp_files = []

        if file_count > 0:
            for i in range(file_count):
                file_key = f'file{i}'
                if file_key in request.files:
                    file = request.files[file_key]
                    if file and file.filename:
                        # Check file size (50MB limit)
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)

                        if file_size > 50 * 1024 * 1024:
                            return jsonify({'error': f'File {file.filename} exceeds 50MB limit'}), 400

                        # Save to temp file
                        file_ext = os.path.splitext(file.filename)[1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                            file.save(tmp_file.name)
                            temp_files.append(tmp_file.name)
                            uploaded_files.append({
                                'filename': file.filename,
                                'path': tmp_file.name,
                                'size': file_size
                            })

                        logger.info(f"Saved file: {file.filename} ({file_size} bytes) to {tmp_file.name}")

        # Build query text with file context
        query_text = text
        if uploaded_files:
            query_text += f"\n\n📎 Archivos adjuntos ({len(uploaded_files)}):\n"
            for file_info in uploaded_files:
                query_text += f"- {file_info['filename']} ({file_info['size']} bytes): {file_info['path']}\n"
            query_text += "\nPor favor, analiza estos archivos y proporciona información relevante."

        logger.info(f"Query with {len(uploaded_files)} files (session {session_id}): {text[:100]}...")

        try:
            # Query Claude Code with session (pass uploaded file paths)
            response = query_claude_code(query_text, session_id=session_id, user_id=user_id, file_paths=temp_files)

            return jsonify({
                'query': text,
                'response': response,
                'files_processed': len(uploaded_files),
                'session_id': session_id,
                'user_id': user_id
            })

        finally:
            # Clean up temp files
            for temp_path in temp_files:
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Deleted temp file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_path}: {e}")

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


# ============================================================================
# FILE STORAGE ENDPOINTS (MinIO + PostgreSQL)
# ============================================================================

from file_storage import get_file_storage_manager

# Initialize file storage manager
try:
    file_storage = get_file_storage_manager()
    logger.info("File storage manager initialized")
except Exception as e:
    logger.error(f"Failed to initialize file storage: {e}")
    file_storage = None


@app.route('/files/upload-url', methods=['POST'])
def generate_file_upload_url():
    """
    Generate presigned URL for direct file upload to MinIO

    POST /files/upload-url
    {
        "filename": "specs.pdf",
        "contentType": "application/pdf",
        "project_id": "INSAGTEC-6598",
        "visibility": "private"
    }

    Returns:
    {
        "upload_url": "https://...",
        "object_key": "projects/INSAGTEC-6598/...",
        "file_id": "uuid",
        "bucket": "insa-projects",
        "expires_in": 3600
    }
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Authenticate user (supports both JWT and legacy tokens)
        user_info = get_auth_token_and_verify(request)
        if not user_info:
            return jsonify({'error': 'Authentication required'}), 401

        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()

        filename = data.get('filename')
        content_type = data.get('contentType', 'application/octet-stream')
        project_id = data.get('project_id')
        visibility = data.get('visibility', 'private')

        if not filename:
            return jsonify({'error': 'filename required'}), 400

        # Generate upload URL
        result = file_storage.generate_upload_url(
            filename=filename,
            content_type=content_type,
            project_id=project_id,
            visibility=visibility
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Upload URL generation error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/files/metadata', methods=['POST'])
def save_file_metadata():
    """
    Save file metadata after successful upload to MinIO

    POST /files/metadata
    {
        "file_id": "uuid",
        "filename": "specs.pdf",
        "bucket": "insa-projects",
        "object_key": "projects/INSAGTEC-6598/...",
        "file_size": 2048000,
        "mime_type": "application/pdf",
        "project_id": 1,
        "tags": ["specs", "separator"],
        "visibility": "private"
    }
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Authenticate user (supports both JWT and legacy tokens)
        user_info = get_auth_token_and_verify(request)
        if not user_info:
            return jsonify({'error': 'Authentication required'}), 401

        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Validate required fields
        required = ['file_id', 'filename', 'bucket', 'object_key', 'file_size']
        for field in required:
            if field not in data:
                return jsonify({'error': f'{field} required'}), 400

        # Save metadata
        result = file_storage.save_file_metadata(
            file_id=data['file_id'],
            filename=data['filename'],
            bucket=data['bucket'],
            object_key=data['object_key'],
            file_size=int(data['file_size']),
            mime_type=data.get('mime_type', 'application/octet-stream'),
            uploaded_by=user_info['user_id'],
            project_id=data.get('project_id'),
            tags=data.get('tags', []),
            visibility=data.get('visibility', 'private')
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"File metadata save error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/files', methods=['GET'])
def list_files():
    """
    List files accessible to user

    GET /files?project_id=1&tags=specs&visibility=private&limit=50&offset=0

    Returns:
    {
        "files": [...],
        "total": 42,
        "limit": 50,
        "offset": 0
    }
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Get auth token
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        user_info = auth_mgr.verify_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401

        # Get filters
        project_id = request.args.get('project_id', type=int)
        tags = request.args.getlist('tags')  # Can pass multiple
        visibility = request.args.get('visibility')
        ai_generated = request.args.get('ai_generated', type=lambda x: x.lower() == 'true')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        # List files
        result = file_storage.list_files(
            user_id=user_info['user_id'],
            project_id=project_id,
            tags=tags if tags else None,
            visibility=visibility,
            ai_generated=ai_generated,
            limit=min(limit, 100),  # Max 100
            offset=offset
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"List files error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/files/<file_id>', methods=['GET'])
def get_file_details(file_id):
    """
    Get detailed file information

    GET /files/{file_id}

    Returns file metadata
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Get auth token
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        user_info = auth_mgr.verify_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401

        # Get file details
        file_data = file_storage.get_file_details(file_id, user_info['user_id'])

        if not file_data:
            return jsonify({'error': 'File not found or access denied'}), 404

        return jsonify(file_data)

    except Exception as e:
        logger.error(f"Get file details error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/files/<file_id>/download', methods=['GET'])
def download_file(file_id):
    """
    Generate presigned download URL

    GET /files/{file_id}/download

    Returns:
    {
        "download_url": "https://...",
        "expires_in": 3600,
        "filename": "specs.pdf"
    }
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Get auth token
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        user_info = auth_mgr.verify_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401

        # Get file details first
        file_data = file_storage.get_file_details(file_id, user_info['user_id'])
        if not file_data:
            return jsonify({'error': 'File not found or access denied'}), 404

        # Generate download URL
        download_url = file_storage.generate_download_url(
            file_id,
            user_info['user_id'],
            expires=3600
        )

        if not download_url:
            return jsonify({'error': 'Failed to generate download URL'}), 500

        return jsonify({
            'download_url': download_url,
            'expires_in': 3600,
            'filename': file_data['filename'],
            'file_size': file_data['file_size']
        })

    except Exception as e:
        logger.error(f"Download URL generation error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/files/<file_id>/share', methods=['POST'])
def share_file_endpoint(file_id):
    """
    Share file with other users

    POST /files/{file_id}/share
    {
        "user_ids": ["uuid1", "uuid2"],
        "permission": "read",
        "expires_at": "2025-12-31T23:59:59Z"
    }
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Authenticate user (supports both JWT and legacy tokens)
        user_info = get_auth_token_and_verify(request)
        if not user_info:
            return jsonify({'error': 'Authentication required'}), 401

        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()

        user_ids = data.get('user_ids', [])
        permission = data.get('permission', 'read')
        expires_at = data.get('expires_at')

        if not user_ids:
            return jsonify({'error': 'user_ids required'}), 400

        # Share file
        result = file_storage.share_file(
            file_id=file_id,
            shared_by=user_info['user_id'],
            shared_with=user_ids,
            permission=permission,
            expires_at=expires_at
        )

        return jsonify(result)

    except (ValueError, PermissionError) as e:
        return jsonify({'error': str(e)}), 403

    except Exception as e:
        logger.error(f"File share error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/files/<file_id>', methods=['DELETE'])
def delete_file_endpoint(file_id):
    """
    Delete file (soft delete)

    DELETE /files/{file_id}
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        # Get auth token
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401

        user_info = auth_mgr.verify_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401

        # Delete file
        success = file_storage.delete_file(file_id, user_info['user_id'])

        if success:
            return jsonify({'success': True, 'message': 'File deleted'})
        else:
            return jsonify({'error': 'File not found or permission denied'}), 404

    except Exception as e:
        logger.error(f"File delete error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# AI Agent File Access Endpoints
@app.route('/agent/files/<file_id>', methods=['GET'])
def agent_get_file(file_id):
    """
    AI Agent file retrieval

    GET /agent/files/{file_id}?agent=dimensionamiento&session_id=user_1

    Returns:
    {
        "file_path": "/tmp/cached_uuid.pdf",
        "filename": "specs.pdf",
        "metadata": {...}
    }
    """
    if not file_storage:
        return jsonify({'error': 'File storage not available'}), 503

    try:
        agent = request.args.get('agent')
        session_id = request.args.get('session_id')

        if not agent or not session_id:
            return jsonify({'error': 'agent and session_id required'}), 400

        # Extract user_id from session_id (format: "user_UUID")
        if session_id.startswith('user_'):
            user_id = session_id[5:]  # Remove "user_" prefix
        else:
            return jsonify({'error': 'Invalid session_id format'}), 400

        # Get file details
        file_data = file_storage.get_file_details(file_id, user_id)
        if not file_data:
            return jsonify({'error': 'File not found or access denied'}), 404

        # Download file to temp cache
        import tempfile
        download_url = file_storage.generate_download_url(file_id, user_id, expires=300)

        if not download_url:
            return jsonify({'error': 'Failed to generate download URL'}), 500

        # Download to temp file
        import requests
        response = requests.get(download_url)
        response.raise_for_status()

        file_ext = os.path.splitext(file_data['filename'])[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(response.content)
            temp_path = tmp_file.name

        # Log access
        file_storage._log_file_access(file_id, user_id, 'view', agent=agent)

        return jsonify({
            'file_path': temp_path,
            'filename': file_data['filename'],
            'file_size': file_data['file_size'],
            'mime_type': file_data['mime_type'],
            'metadata': file_data
        })

    except Exception as e:
        logger.error(f"Agent file access error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


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

    # Initialize and start Prometheus metrics server (if available)
    if PROMETHEUS_ENABLED:
        try:
            metrics_port = int(os.getenv('PROMETHEUS_PORT', '9091'))
            initialize_metrics(version='1.0.0', environment='production')
            start_metrics_server(port=metrics_port)
            logger.info(f"✅ Prometheus metrics server started on port {metrics_port}")
            logger.info(f"   Access metrics at: http://localhost:{metrics_port}/metrics")
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {e}")
    else:
        logger.info("⚠️ Prometheus metrics disabled (prometheus_metrics module not found)")

    # Register Command Center V4 API extensions
    try:
        from v4_api_extensions import register_v4_endpoints
        register_v4_endpoints(app, session_mgr)
        logger.info("✅ Command Center V4 API extensions registered")
    except Exception as e:
        logger.error(f"Failed to register V4 API extensions: {e}")

    # Register Command Center V4 Navigation API extensions
    try:
        from v4_api_extensions_navigation import register_navigation_endpoints
        register_navigation_endpoints(app)
        logger.info("✅ Command Center V4 Navigation API extensions registered")
    except Exception as e:
        logger.error(f"Failed to register V4 Navigation API extensions: {e}")

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )
